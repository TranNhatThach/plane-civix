/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useForm, Controller } from "react-hook-form";
import { Lightbulb } from "lucide-react";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { CustomSelect } from "@plane/ui";
import type { IFormattedInstanceConfiguration, TInstanceAIConfigurationKeys } from "@plane/types";
import { ControllerInput } from "@/components/common/controller-input";
import { useInstance } from "@/hooks/store";

type AIFormValues = Record<TInstanceAIConfigurationKeys, string>;

export const LLM_PROVIDERS = [
  {
    key: "openai",
    label: "OpenAI",
    defaultModel: "o3-mini",
    defaultBaseUrl: "https://api.openai.com/v1",
    models: ["o3-mini", "o1", "gpt-4o", "gpt-4o-mini", "gpt-4.5-preview"],
  },
  {
    key: "anthropic",
    label: "Anthropic",
    defaultModel: "claude-3-7-sonnet",
    models: ["claude-3-7-sonnet", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest"],
  },
  {
    key: "gemini",
    label: "Google Gemini",
    defaultModel: "gemini-2.0-flash",
    models: ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-pro-exp-02-05"],
  },
  {
    key: "deepseek",
    label: "DeepSeek",
    defaultModel: "deepseek-reasoner",
    defaultBaseUrl: "https://api.deepseek.com/v1",
    models: ["deepseek-reasoner", "deepseek-chat", "deepseek-r1", "deepseek-v3"],
  },
  {
    key: "fpt",
    label: "FPT AI Factory",
    defaultModel: "glm-5.2",
    defaultBaseUrl: "https://api.fpt.ai/v1",
    models: [
      "GLM-5.1",
      "GLM-4.7",
      "DeepSeek-V4-Flash",
      "Kimi-K2.5",
      "Llama-3.3-70B-Instruct",
      "Qwen2.5-Coder-32B-Instruct",
      "gemma-3-27b-it",
    ],
  },
  {
    key: "groq",
    label: "Groq (High-Speed Inference)",
    defaultModel: "deepseek-r1-distill-llama-70b",
    defaultBaseUrl: "https://api.groq.com/openai/v1",
    models: ["deepseek-r1-distill-llama-70b", "llama-3.3-70b-versatile", "qwen-2.5-coder-32b", "llama-3.1-8b-instant"],
  },
  {
    key: "openrouter",
    label: "OpenRouter",
    defaultModel: "deepseek/deepseek-r1",
    defaultBaseUrl: "https://openrouter.ai/api/v1",
    models: [
      "deepseek/deepseek-r1",
      "anthropic/claude-3.7-sonnet",
      "openai/gpt-4o",
      "google/gemini-2.0-flash-001",
      "meta-llama/llama-3.3-70b-instruct",
    ],
  },
  {
    key: "ollama",
    label: "Ollama / Local Server",
    defaultModel: "deepseek-r1:70b",
    defaultBaseUrl: "http://localhost:11434/v1",
    models: ["deepseek-r1:70b", "deepseek-r1:14b", "llama3.3:70b", "qwen2.5-coder:32b", "phi4"],
  },
  {
    key: "custom",
    label: "Custom Base URL",
    defaultModel: "deepseek-r1",
    defaultBaseUrl: "http://localhost:8000/v1",
    models: ["deepseek-r1", "deepseek-v3", "llama3.3:70b", "qwen2.5-coder:32b"],
  },
];

export function InstanceAIForm({ config }: { config: Partial<IFormattedInstanceConfiguration> }) {
  const { updateInstanceConfigurations } = useInstance();

  const {
    handleSubmit,
    control,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<AIFormValues>({
    defaultValues: {
      LLM_PROVIDER: config["LLM_PROVIDER"] || "openai",
      LLM_MODEL: config["LLM_MODEL"] || "gpt-4o-mini",
      LLM_BASE_URL: config["LLM_BASE_URL"] || "",
      LLM_API_KEY: config["LLM_API_KEY"] || "",
    },
  });

  const providerKey = (watch("LLM_PROVIDER") || "openai").toLowerCase();
  const currentProvider = LLM_PROVIDERS.find((p) => p.key === providerKey) || LLM_PROVIDERS[0];

  const handleProviderChange = (key: string) => {
    setValue("LLM_PROVIDER", key);
    const target = LLM_PROVIDERS.find((p) => p.key === key);
    if (target) setValue("LLM_MODEL", target.defaultModel);
  };

  const onSubmit = async (data: AIFormValues) => {
    await updateInstanceConfigurations(data)
      .then(() => setToast({ type: TOAST_TYPE.SUCCESS, title: "Success", message: "AI Settings updated successfully" }))
      .catch((err) => console.error(err));
  };

  return (
    <div className="space-y-8">
      <div className="space-y-6">
        <div>
          <div className="pb-1 text-18 font-medium text-primary">LLM Provider Settings</div>
          <div className="text-13 text-tertiary">Configure the AI provider, model, and endpoint API key.</div>
        </div>

        {/* Provider Select */}
        <div className="flex max-w-xl flex-col gap-1.5">
          <h4 className="text-13 font-medium text-tertiary">Select Provider</h4>
          <Controller
            control={control}
            name="LLM_PROVIDER"
            render={({ field: { value } }) => (
              <CustomSelect
                value={value || "openai"}
                label={currentProvider.label}
                onChange={handleProviderChange}
                buttonClassName="rounded-md border-subtle w-full"
                input
              >
                {LLM_PROVIDERS.map((p) => (
                  <CustomSelect.Option key={p.key} value={p.key} className="w-full">
                    {p.label}
                  </CustomSelect.Option>
                ))}
              </CustomSelect>
            )}
          />
        </div>

        {/* Fields */}
        <div className="grid grid-cols-1 gap-x-12 gap-y-6 lg:grid-cols-2">
          <div className="flex flex-col gap-2">
            <ControllerInput
              control={control}
              type="text"
              name="LLM_MODEL"
              label="LLM Model"
              placeholder={currentProvider.defaultModel}
              error={Boolean(errors.LLM_MODEL)}
              required={false}
            />
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-11 text-tertiary">Presets:</span>
              {currentProvider.models.map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setValue("LLM_MODEL", m)}
                  className="rounded bg-layer-2 px-2 py-0.5 text-caption-sm-regular text-secondary transition-colors hover:bg-layer-3"
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <ControllerInput
            control={control}
            type="password"
            name="LLM_API_KEY"
            label="API Key"
            placeholder="sk-..."
            error={Boolean(errors.LLM_API_KEY)}
            required={false}
          />

          <div className="lg:col-span-2">
            <ControllerInput
              control={control}
              type="text"
              name="LLM_BASE_URL"
              label="Custom Base URL (Optional)"
              description={`Endpoint URL override. Default: ${currentProvider.defaultBaseUrl || "Provider default"}`}
              placeholder={currentProvider.defaultBaseUrl || "http://localhost:11434/v1"}
              error={Boolean(errors.LLM_BASE_URL)}
              required={false}
            />
          </div>
        </div>
      </div>

      <div className="flex flex-col items-start gap-4 border-t border-subtle pt-4">
        <Button variant="primary" size="lg" onClick={handleSubmit(onSubmit)} loading={isSubmitting}>
          {isSubmitting ? "Saving..." : "Save changes"}
        </Button>
        <div className="inline-flex items-center gap-1.5 rounded-sm border border-accent-subtle bg-accent-subtle px-4 py-2 text-caption-sm-regular text-accent-secondary">
          <Lightbulb className="size-4" />
          <span>
            Support for <strong>FPT AI Factory</strong>, <strong>DeepSeek</strong>, <strong>Google Gemini</strong>,{" "}
            <strong>OpenAI</strong>, <strong>Anthropic</strong>, <strong>Groq</strong>, <strong>OpenRouter</strong>, and{" "}
            <strong>Custom Base URLs</strong> enabled.
          </span>
        </div>
      </div>
    </div>
  );
}
