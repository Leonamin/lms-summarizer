import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { SettingsResponse } from "../types";
import type { Cache, Course, Detail, Query } from "../lib/courses";
export function useCourseCatalog(
  settings: SettingsResponse | null,
  report: (cause: unknown) => void,
) {
  const [courses, setCourses] = useState<Cache<Course[]> | null>(null);
  const [course, setCourse] = useState("");
  const [detail, setDetail] = useState<Cache<Detail | null> | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [query, setQuery] = useState<Query | null>(null);
  const [message, setMessage] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const epoch = useRef(0);
  const courseRef = useRef(course);
  courseRef.current = course;

  useEffect(() => {
    epoch.current++;
    setCourses(null);
    setDetail(null);
    setCourse("");
    setSelected([]);
    setQuery(null);
    const gen = epoch.current;
    api<Cache<Course[]>>("/courses")
      .then((result) => {
        if (gen === epoch.current) {
          setCourses(result);
          setQuery(result.refresh);
        }
      })
      .catch(report);
  }, [settings?.settings.student_id, settings?.revision]);

  useEffect(() => {
    setDetail(null);
    setSelected([]);
    if (!course) return;
    let isAlive = true;
    const gen = epoch.current;
    api<Cache<Detail | null>>("/courses/" + course + "/lectures")
      .then((result) => {
        if (isAlive && gen === epoch.current) {
          setDetail(result);
          setQuery(result.refresh);
        }
      })
      .catch(report);
    return () => {
      isAlive = false;
    };
  }, [course]);

  useEffect(() => {
    if (!query || !["queued", "running"].includes(query.status)) return;
    let isAlive = true;
    const gen = epoch.current;
    const poll = async () => {
      try {
        const result = await api<Query>("/course-refreshes/" + query.id);
        if (!isAlive || gen !== epoch.current) return;
        setQuery(result);
        if (result.status === "completed") {
          if (result.course_id) {
            const cache = await api<Cache<Detail | null>>(
              "/courses/" + result.course_id + "/lectures",
            );
            if (gen === epoch.current && result.course_id === courseRef.current)
              setDetail(cache);
          } else {
            const cache = await api<Cache<Course[]>>("/courses");
            if (gen === epoch.current) setCourses(cache);
          }
          if (gen === epoch.current) setMessage("목록을 갱신했습니다.");
        } else if (["failed", "interrupted"].includes(result.status))
          setMessage(
            "조회가 " +
              (result.status === "interrupted" ? "중단" : "실패") +
              "되었습니다. 계정·Chrome 진단을 확인한 뒤 다시 갱신해 주세요. (" +
              result.error_code +
              ")",
          );
      } catch (cause) {
        if (isAlive) report(cause);
      }
    };
    const timer = setInterval(() => void poll(), 1000);
    return () => {
      isAlive = false;
      clearInterval(timer);
    };
  }, [query?.id, query?.status, course]);

  async function refresh(id: string | null) {
    setIsRefreshing(true);
    try {
      setQuery(
        await api<Query>("/course-refreshes", {
          method: "POST",
          body: JSON.stringify({ course_id: id }),
        }),
      );
      setMessage("다운로드 단계 사이에서 목록을 조회합니다.");
    } catch (cause) {
      report(cause);
    } finally {
      setIsRefreshing(false);
    }
  }

  return {
    courses,
    course,
    setCourse,
    detail,
    selected,
    setSelected,
    query,
    message,
    setMessage,
    isRefreshing,
    refresh,
  };
}
