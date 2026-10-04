export const endStageOptions = [
  { value: "4", label: "요약 / 프롬프트 준비" },
  { value: "3", label: "음성 인식까지만" },
  { value: "2", label: "오디오 변환까지만" },
  { value: "1", label: "다운로드까지만" },
];
export const fileEndStageOptions = endStageOptions.filter(
  (option) => option.value !== "1",
);
