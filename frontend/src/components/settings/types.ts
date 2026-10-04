import type { ReactNode } from "react";
import type { Settings } from "../../types";
type Model = { id: string; label: string };
type Provider = { default_model: string; models: Model[] };
export type Catalog = {
  summary: Record<string, Provider>;
  stt: Record<string, Provider>;
  summary_modes: Record<string, string>;
  subject_categories: string[];
  default_prompt: string;
};

export type ChangeSetting = <K extends keyof Settings>(
  name: K,
  value: Settings[K],
) => void;
export type SettingsFieldsProps = {
  draft: Settings;
  change: ChangeSetting;
  isSaving: boolean;
};
export type SecretRenderer = (name: string, label: string) => ReactNode;
