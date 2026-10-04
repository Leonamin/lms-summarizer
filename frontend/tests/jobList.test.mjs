import { test } from "node:test";
import assert from "node:assert/strict";
import { getJobPage, sortJobs } from "../src/lib/jobList.ts";
import { getCourseSources } from "../src/lib/courses.ts";
const jobs = Array.from({ length: 29 }, (_, index) => ({
  id: String(index),
  created_at: String(index).padStart(2, "0"),
  display_name: "강의 " + index,
  status: "completed",
  attempts: [],
}));

test("linked jobs reveal the right page under either date order and page size", () => {
  assert.equal(getJobPage(jobs, "0", { key: "created", dir: "desc" }, 20), 2);
  assert.equal(getJobPage(jobs, "0", { key: "created", dir: "desc" }, 10), 3);
  assert.equal(getJobPage(jobs, "0", { key: "created", dir: "asc" }, 20), 1);
  assert.equal(
    getJobPage(jobs, "missing", { key: "created", dir: "asc" }, 20),
    null,
  );
});

test("sorting does not mutate the shared streamed job collection", () => {
  const original = jobs.map(({ id }) => id);
  assert.equal(sortJobs(jobs, { key: "created", dir: "desc" })[0].id, "28");
  assert.deepEqual(
    jobs.map(({ id }) => id),
    original,
  );
});

test("course submission retains selected order and course/week metadata", () => {
  const detail = {
    course_name: "선형대수",
    weeks: [
      { title: "1주차", lectures: [{ title: "행렬", url: "matrix" }] },
      { title: "2주차", lectures: [{ title: "벡터", url: "vector" }] },
    ],
  };
  assert.deepEqual(getCourseSources(detail, ["vector", "matrix"]), [
    {
      reference: "vector",
      display_name: "벡터",
      course_name: "선형대수",
      week_title: "2주차",
    },
    {
      reference: "matrix",
      display_name: "행렬",
      course_name: "선형대수",
      week_title: "1주차",
    },
  ]);
});
