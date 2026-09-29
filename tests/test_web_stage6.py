import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.core.models.jobs import StageResult, Source
from src.core.models.settings import UserContext
from src.core.services.jobs import JobService
from src.web.app import create_app
from src.web.config import WebConfig
from test_job_service import FakeExecutor

class CatalogExecutor(FakeExecutor):
    def execute(self, command, cancelled):
        if command.catalog_query is not None:
            values=json.loads(command.settings_json)
            time.sleep(.15)
            if values.get('student_id')=='fail':
                raise RuntimeError('private password and signed URL')
            if values.get('student_id')=='slow':
                time.sleep(20)
            course=command.catalog_query['course']
            data=([{'id':'123','long_name':'자료구조','href':'/courses/123','term':'2026-2','is_favorited':True}] if not course else
                  {'course_name':'자료구조','professors':'테스트 교수','weeks':[{'title':'1주차','week_number':1,'lectures':[
                    {'title':'배열','url':'https://canvas.ssu.ac.kr/courses/123/lecture/1','duration':'10:00','attendance':'attended','completion':'complete','is_video':True,'is_upcoming':False,'type':'movie'},
                    {'title':'예정','url':'https://canvas.ssu.ac.kr/courses/123/lecture/2','duration':None,'attendance':'none','completion':'incomplete','is_video':True,'is_upcoming':True,'type':'movie'},
                    {'title':'퀴즈','url':'https://canvas.ssu.ac.kr/courses/123/quiz/3','duration':None,'attendance':'none','completion':'incomplete','is_video':False,'is_upcoming':False,'type':'quiz'}]}]})
            return StageResult(command.token,kind='catalog',data=data)
        return super().execute(command,cancelled)

def catalog_service(root, **kwargs):
    return JobService(root,executor_factory=CatalogExecutor,shutdown_grace=.1,cancel_grace=.1,**kwargs)

class Stage6Tests(unittest.TestCase):
    def app(self, root):
        return create_app(WebConfig(data_dir=root/'data',models_dir=root/'models',static_dir=root/'static',allowed_hosts=('testserver',),min_free_bytes=0),service_factory=catalog_service)
    def account(self, client, account='one'):
        current=client.get('/api/v1/settings').json()
        result=client.patch('/api/v1/settings',json={'expected_revision':current['revision'],'settings':current['settings']|{'student_id':account}})
        self.assertEqual(result.status_code,200,result.text)
        client.put('/api/v1/secrets/lms_password',json={'value':'private password'})
        return client.get('/api/v1/settings').json()
    def wait(self,client,query,statuses=('completed',)):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            result=client.get('/api/v1/course-refreshes/'+query).json()
            if result['status'] in statuses:return result
            time.sleep(.02)
        self.fail(str(result))
    def test_catalog_settings_preview_all_providers_and_validation(self):
        from src.core.prompts import build_prompt
        with tempfile.TemporaryDirectory() as directory,TestClient(self.app(Path(directory))) as client:
            catalog=client.get('/api/v1/catalog').json()
            self.assertEqual(set(catalog['summary']),{'clipboard','gemini','openai','claude','grok','custom'})
            self.assertEqual(set(catalog['stt']),{'faster-whisper','openai-whisper','openai-compatible','returnzero'})
            for engine,item in catalog['summary'].items():
                state=client.get('/api/v1/settings').json()
                config=state['settings']|{'ai_engine':engine,'ai_model':item['default_model'],'summary_mode':'detailed','subject_custom':'자료구조','request_timeout':60}
                result=client.patch('/api/v1/settings',json={'expected_revision':state['revision'],'settings':config})
                self.assertEqual(result.status_code,200,result.text)
                self.assertEqual(client.post('/api/v1/prompt-preview',json=config).json()['text'],build_prompt('detailed','자동 감지','자료구조'))
            for engine,item in catalog['stt'].items():
                state=client.get('/api/v1/settings').json()
                config=state['settings']|{'stt_engine':engine,'stt_model':item['default_model'],'stt_base_url':'http://localhost:9000/v1','stt_compatible_model':'fixture','stt_params':{'device':'cpu','compute_type':'int8','initial_prompt':'힌트','language':'ko','repeat_threshold':5,'vad_filter':True}}
                self.assertEqual(client.patch('/api/v1/settings',json={'expected_revision':state['revision'],'settings':config}).status_code,200)
            for name in client.get('/api/v1/settings').json()['secrets']:
                self.assertEqual(client.put('/api/v1/secrets/'+name,json={'value':'dont-show-me'}).status_code,200)
                self.assertEqual(client.delete('/api/v1/secrets/'+name).status_code,200)
            self.assertNotIn('dont-show-me',client.get('/api/v1/settings').text)
            for invalid in ({'stt_params':{'api_key':'dont-show-me'}},{'base_url':'https://user:dont-show-me@example.com/v1'},{'request_timeout':0},{'summary_mode':'oops'},{'stt_params':{'repeat_threshold':'oops'}}):
                state=client.get('/api/v1/settings').json()
                response=client.patch('/api/v1/settings',json={'expected_revision':state['revision'],'settings':state['settings']|invalid})
                self.assertEqual(response.status_code,422)
                self.assertNotIn('dont-show-me',response.text)
    def test_course_cache_account_boundary_queue_serialization_and_url_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with TestClient(self.app(root)) as client:
                self.assertEqual(client.post('/api/v1/course-refreshes',json={}).status_code,422)
                state=self.account(client)
                first=client.post('/api/v1/course-refreshes',json={}).json()
                duplicate=client.post('/api/v1/course-refreshes',json={}).json()
                self.assertEqual(first['id'],duplicate['id'])
                self.assertEqual(client.delete('/api/v1/secrets/lms_password').status_code,409)
                self.wait(client,first['id'])
                courses=client.get('/api/v1/courses').json()
                self.assertFalse(courses['expired']);self.assertEqual(courses['data'][0]['id'],'123')
                query=client.post('/api/v1/course-refreshes',json={'course_id':'123'}).json()
                self.wait(client,query['id'])
                detail=client.get('/api/v1/courses/123/lectures').json()
                self.assertEqual(len(detail['data']['weeks'][0]['lectures']),3)
                # URL download shares the query worker: both cannot be running at once.
                query=client.post('/api/v1/course-refreshes',json={}).json()
                self.wait(client,query['id'],('running',))
                submission=client.post('/api/v1/jobs',json={'settings_revision':state['settings_revision'],'end_stage':1,'sources':[{'kind':'url','reference':'https://canvas.ssu.ac.kr/courses/123/lecture/1'}]},headers={'Idempotency-Key':'urls'})
                self.assertEqual(submission.status_code,202,submission.text)
                job_id=submission.json()['job_ids'][0]
                self.assertEqual(client.get('/api/v1/jobs/'+job_id).json()['status'],'queued')
                self.wait(client,query['id'])
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    if client.get('/api/v1/jobs/'+job_id).json()['status']=='completed':break
                    time.sleep(.02)
                self.assertEqual(client.get('/api/v1/jobs/'+job_id).json()['status'],'completed')
                logs=client.get('/api/v1/jobs/'+job_id+'/logs').json()
                self.assertTrue(any(l.get('message')=='stage_completed' for l in logs['logs']))
                self.assertEqual(client.get('/api/v1/jobs/'+job_id+'/logs?cursor='+str(logs['next_cursor'])).json()['logs'],[])
                self.assertNotIn('private password',client.get('/api/v1/jobs/'+job_id+'/logs').text)
                self.assertNotIn('https://canvas',client.get('/api/v1/jobs/'+job_id+'/logs').text)
            with TestClient(self.app(root)) as client:
                self.assertEqual(client.get('/api/v1/courses').json()['data'],courses['data'])
                self.account(client,'two')
                self.assertEqual(client.get('/api/v1/courses').json()['data'],[])
                self.assertIsNone(client.get('/api/v1/courses/123/lectures').json()['data'])
                self.assertEqual(client.post('/api/v1/course-refreshes',json={'course_id':'123'}).status_code,404)
    def test_query_failure_timeout_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with TestClient(self.app(root)) as client:
                self.account(client,'fail')
                query=client.post('/api/v1/course-refreshes',json={}).json()
                result=self.wait(client,query['id'],('failed',))
                self.assertEqual(result['error_code'],'stage_failed')
                self.assertNotIn('private',json.dumps(result))
                self.account(client,'slow')
                query=client.post('/api/v1/course-refreshes',json={}).json()
                self.wait(client,query['id'],('running',))
                pending=client.post('/api/v1/course-refreshes',json={'course_id':None}).json()
                self.assertEqual(pending['id'],query['id'])
                self.account(client,'queued-account')
                queued=client.post('/api/v1/course-refreshes',json={}).json()
                self.assertEqual(queued['status'],'queued')
            with TestClient(self.app(root)) as client:
                self.assertEqual(client.get('/api/v1/course-refreshes/'+query['id']).json()['status'],'interrupted')
                self.wait(client,queued['id'])
                self.account(client)
                client.app.state.service.stage_timeout=.3
                query=client.post('/api/v1/course-refreshes',json={}).json()
                self.wait(client,query['id'])
                self.account(client,'slow')
                query=client.post('/api/v1/course-refreshes',json={}).json()
                result=self.wait(client,query['id'],('failed',))
                self.assertEqual(result['error_code'],'stage_timeout')
    def test_update_check_no_network_error_and_safe_release(self):
        with tempfile.TemporaryDirectory() as directory,TestClient(self.app(Path(directory))) as client:
            import requests
            with patch('requests.get',side_effect=requests.ConnectionError('private')):
                self.assertEqual(client.post('/api/v1/system/update-check',json={}).json(),{'status':'unavailable'})
            with patch('requests.get') as get:
                get.return_value.json.return_value={'tag_name':'v99.0.0','html_url':'https://github.com/Leonamin/lms-summarizer/releases/tag/v99.0.0'}
                self.assertTrue(client.post('/api/v1/system/update-check',json={}).json()['newer'])
                get.return_value.json.return_value['html_url']='javascript:alert(1)'
                self.assertEqual(client.post('/api/v1/system/update-check',json={}).json()['status'],'unavailable')

    def test_cache_expiry_and_server_config_snapshot_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with TestClient(self.app(root)) as client:
                state=self.account(client)
                query=client.post('/api/v1/course-refreshes',json={}).json()
                self.wait(client,query['id'])
                service=client.app.state.service
                with service.lock:
                    raw=service.courses.store.read()
                    for cache in raw['cache'].values():cache['time']='2000-01-01T00:00:00+00:00'
                    service.courses.store.write(raw)
                self.assertTrue(client.get('/api/v1/courses').json()['expired'])
                self.assertEqual(client.get('/api/v1/courses').json()['data'],[])
                old_revision=state['settings_revision']
            config=WebConfig(data_dir=root/'data',models_dir=root/'models',static_dir=root/'static',allowed_hosts=('testserver',),min_free_bytes=0,headless=False)
            with TestClient(create_app(config,service_factory=catalog_service)) as client:
                new=client.get('/api/v1/settings').json()
                self.assertNotEqual(new['settings_revision'],old_revision)
                settings=client.app.state.settings
                self.assertFalse(json.loads(settings.snapshot(new['settings_revision']).settings_json)['headless'])
                self.assertTrue(json.loads(settings.snapshot(old_revision).settings_json)['headless'])

    def test_provider_secrets_are_selected_by_frozen_settings(self):
        with tempfile.TemporaryDirectory() as directory,TestClient(self.app(Path(directory))) as client:
            names=client.get('/api/v1/settings').json()['secrets']
            for name in names:client.put('/api/v1/secrets/'+name,json={'value':'fixture-'+name})
            for engine in ('gemini','openai','claude','grok','custom'):
                current=client.get('/api/v1/settings').json()
                response=client.patch('/api/v1/settings',json={'expected_revision':current['revision'],'settings':current['settings']|{'ai_engine':engine}}).json()
                revision=client.app.state.settings.snapshot(response['settings_revision'])
                refs=dict(revision.secret_versions)
                self.assertEqual(client.app.state.service.secrets.get('local',refs['summary_api_key']),'fixture-summary:'+engine)
            for engine in ('openai-whisper','openai-compatible','returnzero'):
                current=client.get('/api/v1/settings').json()
                response=client.patch('/api/v1/settings',json={'expected_revision':current['revision'],'settings':current['settings']|{'stt_engine':engine}}).json()
                refs=dict(client.app.state.settings.snapshot(response['settings_revision']).secret_versions)
                if engine=='returnzero':
                    self.assertEqual(client.app.state.service.secrets.get('local',refs['returnzero_client_secret']),'fixture-returnzero_client_secret')
                else:self.assertEqual(client.app.state.service.secrets.get('local',refs['stt_api_key']),'fixture-stt:'+engine)

class ProviderBoundaryTests(unittest.TestCase):
    def command(self, root, stage, settings, credentials):
        from src.core.models.jobs import StageCommand, WorkToken
        from src.core.models.stages import PipelineStage
        source=root/'source.txt';source.write_text('lecture fixture')
        return StageCommand(WorkToken('job','attempt','run','gen',PipelineStage(stage)),str(source),str(root/'output'),json.dumps(settings),'fixed prompt',credentials,str(root/'models'))
    def test_each_summary_provider_selected_with_frozen_settings(self):
        import threading
        from src.core.runtime.executor import PipelineExecutor
        from unittest.mock import MagicMock
        for engine in ('gemini','openai','claude','grok','custom'):
            with self.subTest(engine=engine),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                command=self.command(root,4,{'ai_engine':engine,'ai_model':'fixed-model','base_url':'https://api.example/v1','custom_api_mode':'chat','request_timeout':45},{'summary_api_key':'secret-fixture'})
                provider=MagicMock();provider.summarize.return_value='fixture summary'
                with patch('src.summarize_pipeline.providers.create_provider',return_value=provider) as create:
                    result=PipelineExecutor().execute(command,threading.Event())
                self.assertEqual(Path(result.output).read_text(),'fixture summary')
                self.assertEqual(create.call_args.kwargs['model_name'],'fixed-model')
                self.assertEqual(create.call_args.kwargs['request_timeout'],45)
                self.assertEqual(create.call_args.args,(engine,))
                self.assertEqual(create.call_args.kwargs['api_mode'],'chat')
                provider.summarize.assert_called_once_with('lecture fixture','fixed prompt')

    def test_create_provider_forwards_api_mode_only_to_custom(self):
        from unittest.mock import MagicMock
        import src.summarize_pipeline.providers as providers
        gemini, custom = MagicMock(), MagicMock()
        with patch.dict(providers.ENGINE_REGISTRY, {'gemini': gemini, 'custom': custom}):
            providers.create_provider('gemini',api_key='k',model_name='m',base_url='https://x/v1',api_mode='chat')
            self.assertNotIn('api_mode',gemini.call_args.kwargs)
            self.assertNotIn('base_url',gemini.call_args.kwargs)
            providers.create_provider('custom',api_key='k',model_name='m',base_url='https://x/v1',api_mode='responses')
            self.assertEqual(custom.call_args.kwargs['api_mode'],'responses')
            self.assertEqual(custom.call_args.kwargs['base_url'],'https://x/v1')

    def test_custom_provider_api_mode_selects_route(self):
        from unittest.mock import MagicMock
        from src.summarize_pipeline.providers.custom_provider import CustomProvider
        def build(mode):
            fake=MagicMock()
            fake.chat.completions.create.return_value=MagicMock(choices=[MagicMock(message=MagicMock(content='chat-result'))])
            fake.responses.create.return_value=MagicMock(output_text='responses-result')
            with patch('openai.OpenAI',return_value=fake):
                provider=CustomProvider(api_key='k',model_name='m',base_url='https://x/v1',api_mode=mode)
            return provider,fake
        for mode,expected in (('chat','chat-result'),('responses','responses-result')):
            with self.subTest(mode=mode):
                provider,fake=build(mode)
                self.assertEqual(provider.summarize('t','p'),expected)
                if mode=='chat':
                    fake.responses.create.assert_not_called()
                else:
                    fake.chat.completions.create.assert_not_called()
        # auto: 미지원 라우트(404)면 chat으로 폴백한다.
        provider,fake=build('auto')
        unsupported=Exception('no route');unsupported.status_code=404
        fake.responses.create.side_effect=unsupported
        self.assertEqual(provider.summarize('t','p'),'chat-result')
        # auto: 인증/서버 오류는 폴백하지 않고 그대로 올린다.
        provider,fake=build('auto')
        denied=Exception('bad key');denied.status_code=401
        fake.responses.create.side_effect=denied
        with self.assertRaises(Exception):
            provider.summarize('t','p')

    def test_custom_provider_injects_opencode_session_header(self):
        from src.summarize_pipeline.providers.custom_provider import CustomProvider
        headers=CustomProvider._default_headers('https://opencode.ai/zen/go/v1')
        self.assertIn('x-opencode-session',headers)
        self.assertTrue(headers['x-opencode-session'])
        self.assertEqual(CustomProvider._default_headers('https://api.example.com/v1'),{})
        override=CustomProvider._default_headers('https://opencode.ai/zen/go/v1',{'x-opencode-session':'fixed','X-Extra':'1'})
        self.assertEqual(override['x-opencode-session'],'fixed')
        self.assertEqual(override['X-Extra'],'1')
    def test_each_stt_engine_explicit_credentials_and_endpoint(self):
        import threading
        from src.core.runtime.executor import PipelineExecutor
        for engine in ('faster-whisper','openai-whisper','openai-compatible','returnzero'):
            with self.subTest(engine=engine),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                command=self.command(root,3,{'stt_engine':engine,'stt_model':'fixed-model','stt_base_url':'http://localhost:9000/v1','stt_compatible_model':'compatible-model','request_timeout':45,'stt_params':{'initial_prompt':'hint','repeat_threshold':6}}, {'stt_api_key':'fixture-key','returnzero_client_id':'fixture-id','returnzero_client_secret':'fixture-secret'})
                def transcribe(source, output, **kwargs):Path(output).write_text('fixture transcript');return object()
                with patch('src.audio_pipeline.transcriber.transcribe_audio_to_text',side_effect=transcribe) as adapter:
                    result=PipelineExecutor().execute(command,threading.Event())
                self.assertEqual(result.kind,'transcript')
                options=adapter.call_args.kwargs
                self.assertEqual(options['engine'],engine)
                self.assertEqual(options['params']['initial_prompt'],'hint')
                self.assertEqual(options['params']['request_timeout'],45)
                if engine=='openai-compatible':
                    self.assertEqual(options['model_name'],'compatible-model');self.assertEqual(options['params']['base_url'],'http://localhost:9000/v1')
                if engine=='returnzero':
                    self.assertEqual(options['params']['client_id'],'fixture-id');self.assertEqual(options['params']['client_secret'],'fixture-secret')
                if engine=='faster-whisper':
                    self.assertEqual(options['params']['device'],'cpu');self.assertEqual(options['params']['download_root'],str(root/'models'))
    def test_actual_scraper_adapter_serializes_and_closes_on_error(self):
        from dataclasses import replace
        from unittest.mock import AsyncMock
        from src.core.models.courses import Course, CourseDetail, Week, LectureItem, LectureType
        from src.core.services.courses import execute_query
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            command=replace(self.command(root,1,{'student_id':'fixture','chrome_path':'/usr/bin/google-chrome','headless':True},{'lms_password':'fixture-password'}),catalog_query={'course':None})
            course=Course('123','자료구조','/courses/123','2026-2')
            with patch('src.video_pipeline.course_scraper.CourseScraper') as cls:
                scraper=cls.return_value;scraper.start=AsyncMock();scraper.close=AsyncMock();scraper.fetch_courses=AsyncMock(return_value=[course])
                self.assertEqual(execute_query(command).data,[course.to_dict()]);scraper.close.assert_awaited_once()
                scraper.close.reset_mock();scraper.fetch_lectures=AsyncMock(return_value=CourseDetail(course,'자료구조','교수',[Week('1주차',1,[LectureItem('배열','/courses/123/lecture/1',LectureType.MOVIE)])]))
                result=execute_query(replace(command,catalog_query={'course':course.to_dict()}))
                self.assertTrue(result.data['weeks'][0]['lectures'][0]['is_video']);scraper.close.assert_awaited_once()
                scraper.close.reset_mock();scraper.fetch_courses=AsyncMock(side_effect=RuntimeError('private'))
                with self.assertRaises(RuntimeError):execute_query(command)
                scraper.close.assert_awaited_once()

class CourseParserRegressionTests(unittest.TestCase):
    def test_attendance_marker_is_not_a_present_status(self):
        from src.video_pipeline.course_scraper import _attendance_from_classes
        self.assertEqual(_attendance_from_classes('xnmb-attendance_status absent'),'absent')
        self.assertEqual(_attendance_from_classes('xnmb-attendance_status xnmb-attendance_status-late'),'late')
        self.assertEqual(_attendance_from_classes('xnmb-attendance_status attendance'),'attendance')
        self.assertEqual(_attendance_from_classes('xnmb-attendance_status'),'none')
