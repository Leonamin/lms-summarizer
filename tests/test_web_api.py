import io
import json
from pathlib import Path
import tempfile
import time
import unittest
import wave
from fastapi.testclient import TestClient
from src.core.services.jobs import JobService
from src.web.app import create_app
from src.web.config import WebConfig
from test_job_service import FakeExecutor


def fake_service(root, **kwargs):
    return JobService(root, executor_factory=FakeExecutor, cancel_grace=.1, shutdown_grace=.1, **kwargs)

class WebAPITests(unittest.TestCase):
    def make(self, root, factory=fake_service, **kwargs):
        config = WebConfig(data_dir=root/'data', models_dir=root/'models', static_dir=root/'static',
                           allowed_hosts=('testserver',), min_free_bytes=0, **kwargs)
        return create_app(config, service_factory=factory)

    def upload(self, client, content=b'lecture original', filename='lecture.txt'):
        reserved=client.post('/api/v1/uploads', json={'filename':filename,'size':len(content)})
        self.assertEqual(reserved.status_code,201,reserved.text)
        upload_id=reserved.json()['id']
        result=client.put('/api/v1/uploads/'+upload_id+'/content',content=content)
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['status'],'ready')
        return upload_id

    def submit(self, client, upload_id, key='submission', revision=None, end_stage=4):
        revision=revision or client.get('/api/v1/settings').json()['settings_revision']
        result=client.post('/api/v1/jobs',json={'sources':[{'kind':'file','reference':upload_id}],
                         'settings_revision':revision,'end_stage':end_stage},headers={'Idempotency-Key':key})
        self.assertEqual(result.status_code,202,result.text)
        return result.json()['job_ids'][0]

    def wait(self, client, job_id, statuses=('completed',)):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            job=client.get('/api/v1/jobs/'+job_id).json()
            if job['status'] in statuses:return job
            time.sleep(.02)
        self.fail(str(job))

    def test_real_clipboard_upload_submit_content_download_and_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            app=self.make(root, JobService)
            with TestClient(app) as client:
                self.assertEqual(client.get('/api/v1/me').json()['owner_id'],'local')
                upload=self.upload(client,b'\xef\xbb\xbfactual original')
                job_id=self.submit(client,upload)
                self.assertEqual(self.submit(client,upload),job_id)
                job=self.wait(client,job_id)
                self.assertEqual(job['result_kind'],'manual_ready')
                artifact=next(a for a in job['artifacts'] if a['kind']=='prompt')
                content=client.get('/api/v1/artifacts/'+artifact['id']+'/content').json()['text']
                self.assertIn('actual original',content)
                downloaded=client.get('/api/v1/artifacts/'+artifact['id']+'/download')
                self.assertEqual(downloaded.status_code,200)
                self.assertEqual(downloaded.content.decode('utf-8'),content)
                self.assertEqual(client.delete('/api/v1/uploads/'+upload).status_code,409)
                config=client.get('/api/v1/settings').json()
            with TestClient(self.make(root,JobService)) as restarted:
                self.assertEqual(restarted.get('/api/v1/jobs/'+job_id).json()['status'],'completed')
                self.assertEqual(restarted.get('/api/v1/settings').json(),config)
                self.assertEqual(restarted.get('/api/v1/artifacts/'+artifact['id']+'/content').json()['text'],content)

    def test_settings_conflict_secrets_redaction_and_fixed_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with TestClient(self.make(root)) as client:
                before=client.get('/api/v1/settings').json()
                config=before['settings']|{'prompt_mode':'custom','custom_prompt':'fixed prompt'}
                patched=client.patch('/api/v1/settings',json={'expected_revision':before['revision'],'settings':config})
                self.assertEqual(patched.status_code,200,patched.text)
                self.assertEqual(client.patch('/api/v1/settings',json={'expected_revision':before['revision'],'settings':config}).status_code,409)
                self.assertEqual(client.put('/api/v1/secrets/summary:gemini',json={'value':'sensitive-secret'}).status_code,200)
                secret_config=client.get('/api/v1/settings')
                self.assertNotIn('sensitive-secret',secret_config.text)
                self.assertTrue(secret_config.json()['secrets']['summary:gemini']['configured'])
                invalid=client.put('/api/v1/secrets/summary:gemini',json={'value':{'secret':'sensitive-secret'}})
                self.assertEqual(invalid.status_code,422)
                self.assertNotIn('sensitive-secret',invalid.text)
                upload=self.upload(client)
                job_id=self.submit(client,upload,revision=patched.json()['settings_revision'])
                # The submitted immutable snapshot survives later edits.
                current=client.get('/api/v1/settings').json()
                client.patch('/api/v1/settings',json={'expected_revision':current['revision'],
                             'settings':config|{'custom_prompt':'changed prompt'}})
                job=self.wait(client,job_id)
                snapshot=client.get('/api/v1/jobs/'+job_id+'/settings')
                self.assertEqual(snapshot.json()['resolved_prompt'],'fixed prompt')
                self.assertNotIn('chrome_path',snapshot.json()['settings'])
                self.assertNotIn('sensitive-secret',snapshot.text)
                artifact=next(a for a in job['artifacts'] if a['kind']=='prompt')
                self.assertIn('fixed prompt',client.get('/api/v1/artifacts/'+artifact['id']+'/content').json()['text'])
                public=client.get('/api/v1/jobs').text
                self.assertNotIn(str(root),public)
                self.assertNotIn('sensitive-secret',public)

    def test_upload_validation_limits_retry_and_unused_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with TestClient(self.make(root,max_upload_bytes=1000)) as client:
                self.assertEqual(client.post('/api/v1/uploads',json={'filename':'../a.txt','size':5}).status_code,422)
                self.assertEqual(client.post('/api/v1/uploads',json={'filename':'a.exe','size':5}).status_code,422)
                self.assertEqual(client.post('/api/v1/uploads',json={'filename':'a.txt','size':1001}).status_code,413)
                reserved=client.post('/api/v1/uploads',json={'filename':'a.txt','size':3}).json()
                path='/api/v1/uploads/'+reserved['id']
                self.assertEqual(client.put(path+'/content',content=b'ab').status_code,422)
                self.assertEqual(client.get(path).json()['status'],'failed')
                self.assertEqual(client.put(path+'/content',content=b'abc').status_code,200)
                self.assertEqual(client.put(path+'/content',content=b'abc').status_code,409)
                self.assertEqual(client.delete(path).status_code,204)
                self.assertEqual(client.get(path).status_code,404)
                invalid=client.post('/api/v1/uploads',json={'filename':'fake.mp4','size':3}).json()
                self.assertEqual(client.put('/api/v1/uploads/'+invalid['id']+'/content',content=b'abc').status_code,422)
                stream=io.BytesIO()
                with wave.open(stream,'wb') as wav:
                    wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000);wav.writeframes(b'\x00\x00'*100)
                self.upload(client,stream.getvalue(),'audio.wav')

    def test_cancel_retry_attempt_target_and_idempotency(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with TestClient(self.make(root)) as client:
                upload=self.upload(client)
                service=client.app.state.service
                # Occupy the single summary slot so the target remains queued.
                from unittest.mock import patch
                with patch.object(service,'_tick'):
                    job_id=self.submit(client,upload)
                    job=client.get('/api/v1/jobs/'+job_id).json()
                    target={'attempt_id':job['current_attempt_id']}
                    cancelled=client.post('/api/v1/jobs/'+job_id+'/cancel',json=target)
                    self.assertEqual(cancelled.json()['status'],'cancelled')
                    retried=client.post('/api/v1/jobs/'+job_id+'/retry',json=target,headers={'Idempotency-Key':'retry'})
                    self.assertEqual(retried.status_code,202,retried.text)
                    duplicate=client.post('/api/v1/jobs/'+job_id+'/retry',json=target,headers={'Idempotency-Key':'retry'})
                    self.assertEqual(duplicate.json()['current_attempt_id'],retried.json()['current_attempt_id'])
                    self.assertEqual(client.post('/api/v1/jobs/'+job_id+'/retry',json=target,headers={'Idempotency-Key':'different'}).status_code,409)
                done=self.wait(client,job_id)
                self.assertEqual(len(done['attempts']),2)

    def test_origin_host_json_guards_and_spa_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'static').mkdir();(root/'static/index.html').write_text('workspace')
            with TestClient(self.make(root)) as client:
                self.assertEqual(client.get('/').text,'workspace')
                self.assertEqual(client.get('/work/123').text,'workspace')
                self.assertEqual(client.get('/api/v1/missing').status_code,404)
                self.assertEqual(client.get('/api/v1/me',headers={'Host':'attacker.example'}).status_code,400)
                self.assertEqual(client.post('/api/v1/uploads',json={'filename':'a.txt','size':1},headers={'Origin':'https://attacker.example'}).status_code,403)
                self.assertEqual(client.post('/api/v1/uploads',content='{}',headers={'Content-Type':'text/plain'}).status_code,415)
                self.assertEqual(client.post('/api/v1/uploads',content=b'x'*(1024**2+1),headers={'Content-Type':'application/json'}).status_code,413)

    def test_server_restart_interrupts_running_and_restores_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            def slow_service(path, **kwargs):
                return JobService(path, executor_factory=SlowExecutor, shutdown_grace=.1, **kwargs)
            with TestClient(self.make(root,slow_service)) as client:
                first=self.submit(client,self.upload(client),key='first')
                second=self.submit(client,self.upload(client),key='second')
                self.wait(client,first,('running',))
                self.assertEqual(client.get('/api/v1/jobs/'+second).json()['status'],'queued')
            with TestClient(self.make(root)) as client:
                self.assertEqual(client.get('/api/v1/jobs/'+first).json()['status'],'interrupted')
                self.assertTrue(client.get('/api/v1/jobs/'+first).json()['retryable'])
                self.assertEqual(self.wait(client,second)['status'],'completed')

    def test_invalid_stage_and_referenced_secret_deletion_are_safe_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with TestClient(self.make(root)) as client:
                client.put('/api/v1/secrets/lms_password',json={'value':'never-echo-this'})
                config=client.get('/api/v1/settings').json()
                upload=self.upload(client)
                invalid=client.post('/api/v1/jobs',json={'sources':[{'kind':'file','reference':upload}],
                    'settings_revision':config['settings_revision'],'end_stage':2},headers={'Idempotency-Key':'invalid'})
                self.assertEqual(invalid.status_code,422)
                job_id=self.submit(client,upload,revision=config['settings_revision'])
                rejected=client.delete('/api/v1/secrets/lms_password')
                self.assertEqual(rejected.status_code,409,rejected.text)
                self.assertNotIn('never-echo-this',rejected.text)
                self.wait(client,job_id)
                self.assertFalse(list((root/'data/incoming').glob('*')))



class SlowExecutor(FakeExecutor):
    def execute(self, command, cancelled):
        from dataclasses import replace
        values=json.loads(command.settings_json)|{'delay':10}
        return super().execute(replace(command,settings_json=json.dumps(values)),cancelled)
