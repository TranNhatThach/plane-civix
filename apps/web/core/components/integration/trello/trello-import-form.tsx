/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState, useRef } from "react";
import Link from "next/link";
import { observer } from "mobx-react";
import {
  UploadCloud,
  FileCheck2,
  CheckCircle2,
  AlertCircle,
  Layers,
  Tag,
  CheckSquare,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { useProject } from "@/hooks/store/use-project";
import { TrelloIntegrationService, type ITrelloImportResult } from "@/services/integrations/trello.service";

interface Props {
  workspaceSlug: string;
}

interface ITrelloPreview {
  boardName: string;
  listsCount: number;
  cardsCount: number;
  labelsCount: number;
  checklistsCount: number;
  listsNames: string[];
}

const trelloService = new TrelloIntegrationService();

export const TrelloImportForm = observer(function TrelloImportForm({ workspaceSlug }: Props) {
  const { workspaceProjectIds, getProjectById } = useProject();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ITrelloPreview | null>(null);
  const [targetProjectId, setTargetProjectId] = useState<string>("new");
  const [includeClosed, setIncludeClosed] = useState<boolean>(false);
  const [isImporting, setIsImporting] = useState<boolean>(false);
  const [importResult, setImportResult] = useState<ITrelloImportResult | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  const handleFileChange = (file: File) => {
    if (!file.name.endsWith(".json")) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "File không hợp lệ",
        message: "Vui lòng chọn file JSON export từ Trello (.json).",
      });
      return;
    }

    setSelectedFile(file);
    setImportResult(null);

    // Parse preview client-side
    const reader = new FileReader();
    reader.addEventListener("load", (e) => {
      try {
        const json = JSON.parse(e.target?.result as string);
        if (!json || (!json.cards && !json.lists)) {
          setToast({
            type: TOAST_TYPE.ERROR,
            title: "File JSON không đúng chuẩn Trello",
            message: "File không chứa cấu trúc Board của Trello. Vui lòng kiểm tra lại.",
          });
          setPreview(null);
          setSelectedFile(null);
          return;
        }

        const validLists = (json.lists || []).filter((l: any) => !l.closed);
        const validCards = (json.cards || []).filter((c: any) => !c.closed);

        setPreview({
          boardName: json.name || file.name.replace(".json", ""),
          listsCount: validLists.length,
          cardsCount: validCards.length,
          labelsCount: (json.labels || []).length,
          checklistsCount: (json.checklists || []).length,
          listsNames: validLists.map((l: any) => l.name).slice(0, 6),
        });
      } catch (_err) {
        setToast({
          type: TOAST_TYPE.ERROR,
          title: "Lỗi đọc file JSON",
          message: "Không thể đọc nội dung file JSON.",
        });
        setPreview(null);
        setSelectedFile(null);
      }
    });
    reader.readAsText(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleImport = async () => {
    if (!selectedFile) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Chưa chọn file",
        message: "Vui lòng chọn file JSON export từ Trello trước khi import.",
      });
      return;
    }

    setIsImporting(true);
    try {
      const isCreateNew = targetProjectId === "new";
      const result = await trelloService.importTrello(workspaceSlug, isCreateNew ? "global" : targetProjectId, {
        file: selectedFile,
        target_project_id: isCreateNew ? "new" : targetProjectId,
        create_new_project: isCreateNew,
        include_closed: includeClosed,
      });

      setImportResult(result);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Import thành công!",
        message: `Đã chuyển ${result.imported_tasks} task sang Plane thành công.`,
      });
    } catch (err: any) {
      const errMsg = err?.error || err?.message || "Quá trình import thất bại. Vui lòng thử lại.";
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Lỗi Import",
        message: errMsg,
      });
    } finally {
      setIsImporting(false);
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setPreview(null);
    setImportResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="border-border-subtle bg-bg-surface-2 shadow-sm my-4 w-full space-y-5 rounded-lg border p-5">
      {/* Header */}
      <div className="border-border-subtle flex items-center justify-between border-b pb-4">
        <div className="flex items-center space-x-3">
          <div className="bg-sky-500/10 text-sky-500 flex h-10 w-10 items-center justify-center rounded-lg text-20 font-bold">
            📋
          </div>
          <div>
            <h3 className="text-16 font-semibold text-primary">Trello Board Importer</h3>
            <p className="text-13 text-secondary">
              Chuyển toàn bộ danh sách, thẻ công việc, checklist, nhãn màu và deadline từ Trello sang Plane.
            </p>
          </div>
        </div>
      </div>

      {/* Success Result View */}
      {importResult ? (
        <div className="border-emerald-500/30 bg-emerald-500/10 space-y-4 rounded-lg border p-5">
          <div className="flex items-start space-x-3">
            <CheckCircle2 className="text-emerald-500 mt-0.5 h-6 w-6 flex-shrink-0" />
            <div className="space-y-1">
              <h4 className="text-15 text-emerald-400 font-semibold">
                🎉 Import thành công từ bảng &ldquo;{importResult.board_name}&rdquo;!
              </h4>
              <p className="text-13 text-secondary">
                Đã thêm <strong className="text-primary">{importResult.imported_tasks} task</strong>, tạo mới{" "}
                <strong className="text-primary">{importResult.created_states} cột trạng thái</strong> và{" "}
                <strong className="text-primary">{importResult.created_labels} nhãn</strong> vào dự án{" "}
                <strong className="text-primary">
                  {importResult.project_name} ({importResult.project_identifier})
                </strong>
                .
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 pt-2">
            <Link
              href={`/${workspaceSlug}/projects/${importResult.project_id}/issues`}
              className="bg-emerald-600 hover:bg-emerald-700 inline-flex items-center space-x-2 rounded-md px-4 py-2 text-13 font-medium text-white transition"
            >
              <span>Xem Bảng Kanban Dự Án</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Button variant="secondary" onClick={resetForm} className="flex items-center space-x-1.5">
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Import thêm bảng khác</span>
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-5">
          {/* Target Project Selection */}
          <div className="space-y-2">
            <label htmlFor="trello-target-project" className="block text-13 font-medium text-tertiary">
              Dự án đích trên Plane <span className="text-red-500">*</span>
            </label>
            <select
              id="trello-target-project"
              value={targetProjectId}
              onChange={(e) => setTargetProjectId(e.target.value)}
              className="border-border-subtle bg-bg-surface-1 focus:border-custom-primary-500 w-full rounded-md border px-3 py-2 text-13 text-primary focus:outline-none"
            >
              <option value="new">➕ Tự động tạo Dự án mới theo tên Board Trello</option>
              {workspaceProjectIds && workspaceProjectIds.length > 0 && (
                <optgroup label="Hoặc gộp vào dự án có sẵn:">
                  {workspaceProjectIds.map((pId) => {
                    const proj = getProjectById(pId);
                    if (!proj) return null;
                    return (
                      <option key={proj.id} value={proj.id}>
                        [{proj.identifier}] {proj.name}
                      </option>
                    );
                  })}
                </optgroup>
              )}
            </select>
          </div>

          {/* File Upload Dropzone */}
          <div>
            <label htmlFor="trello-file-input" className="mb-1 block text-13 font-medium text-tertiary">
              File JSON Export từ Trello <span className="text-red-500">*</span>
            </label>
            <input
              id="trello-file-input"
              ref={fileInputRef}
              type="file"
              accept=".json"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFileChange(e.target.files[0]);
                }
              }}
            />
            <button
              type="button"
              id="trello-dropzone-button"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`flex w-full cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 transition ${
                isDragging
                  ? "border-custom-primary-500 bg-custom-primary-500/10"
                  : selectedFile
                    ? "border-emerald-500/50 bg-emerald-500/5"
                    : "border-border-subtle hover:border-custom-primary-500/60 bg-bg-surface-1"
              }`}
            >
              {selectedFile ? (
                <div className="flex items-center space-x-3">
                  <FileCheck2 className="text-emerald-500 h-8 w-8" />
                  <div>
                    <p className="text-14 font-semibold text-primary">{selectedFile.name}</p>
                    <p className="text-12 text-secondary">
                      {(selectedFile.size / 1024).toFixed(1)} KB • Bấm để chọn file khác
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-2 text-center">
                  <UploadCloud className="mx-auto h-9 w-9 text-tertiary" />
                  <div>
                    <p className="text-13 font-medium text-primary">
                      Kéo thả file <code className="font-mono text-custom-primary-500">.json</code> vào đây hoặc{" "}
                      <span className="text-custom-primary-500 underline">chọn từ máy tính</span>
                    </p>
                    <p className="mt-0.5 text-11 text-tertiary">
                      💡 Vào Trello ➔ Menu ➔ More ➔ Print and Export ➔ Export as JSON để lấy file.
                    </p>
                  </div>
                </div>
              )}
            </button>
          </div>

          {/* Client-Side Preview Card */}
          {preview && (
            <div className="border-border-subtle bg-bg-surface-1 space-y-3 rounded-lg border p-4">
              <div className="border-border-subtle flex items-center justify-between border-b pb-2">
                <span className="text-13 font-semibold text-primary">
                  📌 Xem trước dữ liệu: <span className="text-custom-primary-500">{preview.boardName}</span>
                </span>
                <span className="text-11 text-tertiary">Đã phân tích cấu trúc</span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-12 sm:grid-cols-4">
                <div className="border-border-subtle bg-bg-surface-2 flex items-center space-x-2 rounded border p-2">
                  <Layers className="text-amber-500 h-4 w-4" />
                  <div>
                    <div className="font-semibold text-primary">{preview.listsCount} Cột</div>
                    <div className="text-10 text-tertiary">States</div>
                  </div>
                </div>
                <div className="border-border-subtle bg-bg-surface-2 flex items-center space-x-2 rounded border p-2">
                  <CheckSquare className="text-blue-500 h-4 w-4" />
                  <div>
                    <div className="font-semibold text-primary">{preview.cardsCount} Thẻ</div>
                    <div className="text-10 text-tertiary">Tasks / Issues</div>
                  </div>
                </div>
                <div className="border-border-subtle bg-bg-surface-2 flex items-center space-x-2 rounded border p-2">
                  <Tag className="text-purple-500 h-4 w-4" />
                  <div>
                    <div className="font-semibold text-primary">{preview.labelsCount} Nhãn</div>
                    <div className="text-10 text-tertiary">Labels</div>
                  </div>
                </div>
                <div className="border-border-subtle bg-bg-surface-2 flex items-center space-x-2 rounded border p-2">
                  <CheckCircle2 className="text-emerald-500 h-4 w-4" />
                  <div>
                    <div className="font-semibold text-primary">{preview.checklistsCount} Danh sách</div>
                    <div className="text-10 text-tertiary">Checklists</div>
                  </div>
                </div>
              </div>

              {preview.listsNames.length > 0 && (
                <div className="pt-1 text-11 text-secondary">
                  <strong>Các cột sẽ được tạo:</strong> {preview.listsNames.join(" ➔ ")}
                  {preview.listsCount > 6 ? ` (+${preview.listsCount - 6} cột khác)` : ""}
                </div>
              )}
            </div>
          )}

          {/* Options */}
          <div className="flex items-center space-x-2 pt-1">
            <input
              id="include-closed-cards"
              type="checkbox"
              checked={includeClosed}
              onChange={(e) => setIncludeClosed(e.target.checked)}
              className="border-gray-300 text-custom-primary-600 focus:ring-custom-primary-500 h-4 w-4 cursor-pointer rounded"
            />
            <label htmlFor="include-closed-cards" className="cursor-pointer text-13 text-secondary">
              Bao gồm cả các thẻ đã lưu trữ (Archived / Closed Cards)
            </label>
          </div>

          {/* Action Button */}
          <div className="border-border-subtle flex items-center justify-between border-t pt-4">
            <div className="flex items-center space-x-1 text-12 text-tertiary">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>Dữ liệu sẽ được ánh xạ tự động vào Kanban Board của Plane.</span>
            </div>

            <Button
              type="button"
              variant="primary"
              onClick={handleImport}
              loading={isImporting}
              disabled={!selectedFile || isImporting}
              className="flex items-center space-x-2"
            >
              <span>🚀 Bắt đầu Import vào Plane</span>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
});
