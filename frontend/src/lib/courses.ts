export type Course = {
  id: string;
  long_name: string;
  term: string;
  is_favorited: boolean;
};
export type Lecture = {
  title: string;
  url: string;
  duration: string | null;
  attendance: string;
  completion: string;
  is_video: boolean;
  is_upcoming: boolean;
  type: string;
};
export type Detail = {
  course_name: string;
  professors: string;
  weeks: { title: string; week_number: number; lectures: Lecture[] }[];
};
export type Query = {
  id: string;
  status: string;
  error_code: string | null;
  course_id: string | null;
};
export type Cache<T> = {
  data: T;
  cache_age_seconds: number | null;
  expired: boolean;
  refresh: Query | null;
};

export type CourseSource = {
  reference: string;
  display_name?: string;
  course_name?: string;
  week_title?: string;
};
export function getCourseSources(
  detail: Detail | null | undefined,
  selected: string[],
): CourseSource[] {
  const lectures = new Map(
    (detail?.weeks ?? []).flatMap((week) =>
      week.lectures.map(
        (lecture) =>
          [
            lecture.url,
            {
              display_name: lecture.title,
              course_name: detail?.course_name ?? "",
              week_title: week.title,
            },
          ] as const,
      ),
    ),
  );
  return selected.map((reference) => ({
    reference,
    ...lectures.get(reference),
  }));
}
