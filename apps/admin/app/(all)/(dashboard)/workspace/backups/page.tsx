/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import Link from "next/link";
import useSWR, { mutate } from "swr";
import { Download, RotateCcw, Trash2, Database, Archive, Send, AlertTriangle, Clock, ShieldCheck } from "lucide-react";

// propel imports
import { Button, getButtonStyling } from "@plane/propel/button";
import { setToast, TOAST_TYPE } from "@plane/propel/toast";
import { InstanceWorkspaceService } from "@plane/services";
import { Loader, CustomSelect, Input } from "@plane/ui";
import { cn } from "@plane/utils";

// components
import { PageWrapper } from "@/components/common/page-wrapper";
import { useWorkspace } from "@/hooks/store";

const instanceWorkspaceService = new InstanceWorkspaceService();

const WorkspaceBackupsPage = observer(function WorkspaceBackupsPage() {
  const [activeTab, setActiveTab] = useState<"backups" | "trash">("backups");
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string>("");
  const [isActionLoading, setIsActionLoading] = useState<boolean>(false);
  const [restoreConfirmBackupId, setRestoreConfirmBackupId] = useState<string | null>(null);
  const [restoreConfirmationInput, setRestoreConfirmationInput] = useState<string>("");

  const { workspaceIds, getWorkspaceById, fetchWorkspaces } = useWorkspace();

  // Load workspaces
  useSWR("INSTANCE_WORKSPACES_FOR_BACKUP", () => fetchWorkspaces(), {
    onSuccess: (data: any) => {
      if (!selectedWorkspaceId && data?.results?.length > 0) {
        setSelectedWorkspaceId(data.results[0].id);
      }
    },
  });

  // Selected workspace object
  const currentWorkspace = selectedWorkspaceId ? getWorkspaceById(selectedWorkspaceId) : null;

  // SWR for backups of selected workspace
  const {
    data: backups = [],
    isLoading: isBackupsLoading,
    mutate: mutateBackups,
  } = useSWR(
    selectedWorkspaceId ? `WORKSPACE_BACKUPS_${selectedWorkspaceId}` : null,
    () => (selectedWorkspaceId ? instanceWorkspaceService.listBackups(selectedWorkspaceId) : []),
    { revalidateOnFocus: false }
  );

  // SWR for trashed workspaces
  const {
    data: trashItems = [],
    isLoading: isTrashLoading,
    mutate: mutateTrash,
  } = useSWR(activeTab === "trash" ? "WORKSPACE_TRASH" : null, () => instanceWorkspaceService.listTrash(), {
    revalidateOnFocus: false,
  });

  // Action: Create manual backup
  const handleCreateBackup = async () => {
    if (!selectedWorkspaceId) return;
    setIsActionLoading(true);
    try {
      await instanceWorkspaceService.createBackup(selectedWorkspaceId);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Sao lưu thành công!",
        message: `Đã tạo bản sao lưu mới cho Workspace ${currentWorkspace?.name ?? ""}.`,
      });
      mutateBackups();
    } catch (err: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Lỗi sao lưu",
        message: err?.error || "Không thể tạo bản sao lưu.",
      });
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Resend handover credentials
  const handleResendHandover = async () => {
    if (!selectedWorkspaceId) return;
    setIsActionLoading(true);
    try {
      const res = await instanceWorkspaceService.resendHandover(selectedWorkspaceId);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Đã gửi lại thông tin bàn giao",
        message: res?.message || `Mật khẩu tạm mới đã được gửi tới email quản trị viên.`,
      });
    } catch (err: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Lỗi gửi email",
        message: err?.error || "Không thể gửi lại thông tin bàn giao.",
      });
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Restore backup
  const handleExecuteRestore = async () => {
    if (!selectedWorkspaceId || !restoreConfirmBackupId || !currentWorkspace) return;
    if (restoreConfirmationInput !== currentWorkspace.slug) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Xác nhận không khớp",
        message: `Vui lòng nhập chính xác slug '${currentWorkspace.slug}' để khôi phục.`,
      });
      return;
    }

    setIsActionLoading(true);
    try {
      await instanceWorkspaceService.restoreBackup(selectedWorkspaceId, restoreConfirmBackupId);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Khôi phục thành công 100%!",
        message: `Workspace ${currentWorkspace.name} đã được khôi phục về thời điểm bản sao lưu. Dữ liệu các workspace khác hoàn toàn độc lập.`,
      });
      setRestoreConfirmBackupId(null);
      setRestoreConfirmationInput("");
      mutateBackups();
    } catch (err: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Khôi phục thất bại",
        message: err?.error || "Đã xảy ra lỗi trong quá trình khôi phục.",
      });
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Delete backup
  const handleDeleteBackup = async (backupId: string) => {
    if (!selectedWorkspaceId || !window.confirm("Bạn có chắc chắn muốn xóa bản sao lưu này?")) return;
    try {
      await instanceWorkspaceService.deleteBackup(selectedWorkspaceId, backupId);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Đã xóa",
        message: "Bản sao lưu đã được dọn dẹp.",
      });
      mutateBackups();
    } catch (err: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Lỗi",
        message: err?.error || "Không thể xóa bản sao lưu.",
      });
    }
  };

  // Action: Restore trashed workspace
  const handleRestoreTrashWorkspace = async (workspaceId: string, name: string) => {
    try {
      await instanceWorkspaceService.restoreWorkspace(workspaceId);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Khôi phục thành công",
        message: `Workspace '${name}' đã được đưa ra khỏi thùng rác và hoạt động bình thường.`,
      });
      mutateTrash();
      mutate("INSTANCE_WORKSPACES_FOR_BACKUP");
    } catch (err: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Lỗi",
        message: err?.error || "Không thể khôi phục workspace.",
      });
    }
  };

  // Action: Purge trashed workspace
  const handlePurgeWorkspace = async (workspaceId: string, slug: string) => {
    const confirmSlug = window.prompt(
      `CẢNH BÁO: Thao tác này sẽ XÓA VĨNH VIỄN workspace '${slug}'. Nhập slug để xác nhận:`
    );
    if (confirmSlug !== slug) return;

    try {
      await instanceWorkspaceService.purgeWorkspace(workspaceId);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Đã xóa vĩnh viễn",
        message: `Workspace '${slug}' đã được xóa triệt để khỏi hệ thống.`,
      });
      mutateTrash();
    } catch (err: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Lỗi",
        message: err?.error || "Không thể xóa vĩnh viễn workspace.",
      });
    }
  };

  return (
    <PageWrapper
      header={{
        title: "Sao lưu & Khôi phục Workspace (Per-Workspace Backups)",
        description:
          "Quản lý sao lưu độc lập, bàn giao quản trị viên và thùng rác 15 ngày cho từng Workspace khách hàng.",
      }}
    >
      <div className="space-y-6">
        {/* Navigation Tabs */}
        <div className="flex items-center justify-between border-b border-subtle pb-3">
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => setActiveTab("backups")}
              className={cn(
                "flex items-center gap-2 border-b-2 pb-2 text-14 font-medium transition-colors",
                activeTab === "backups"
                  ? "border-primary-500 text-primary-500 font-semibold"
                  : "border-transparent text-tertiary hover:text-secondary"
              )}
            >
              <Database className="h-4 w-4" />
              Sao lưu theo Workspace ({workspaceIds.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("trash")}
              className={cn(
                "flex items-center gap-2 border-b-2 pb-2 text-14 font-medium transition-colors",
                activeTab === "trash"
                  ? "border-danger-500 text-danger-500 font-semibold"
                  : "border-transparent text-tertiary hover:text-secondary"
              )}
            >
              <Trash2 className="h-4 w-4" />
              Thùng Rác Workspace (15 Ngày)
              {trashItems?.length > 0 && (
                <span className="bg-danger-500/10 text-danger-500 rounded-full px-2 py-0.5 text-11">
                  {trashItems.length}
                </span>
              )}
            </button>
          </div>
          <Link href="/workspace" className={getButtonStyling("secondary", "sm")}>
            Danh sách Workspace
          </Link>
        </div>

        {/* TAB 1: BACKUPS */}
        {activeTab === "backups" && (
          <div className="space-y-6">
            {/* Top Controls: Workspace selector + Action buttons */}
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-subtle bg-surface-1 p-4">
              <div className="flex items-center gap-3">
                <span className="text-13 font-medium text-secondary">Chọn Workspace:</span>
                <div className="w-64">
                  <CustomSelect
                    value={selectedWorkspaceId}
                    onChange={(val: any) => setSelectedWorkspaceId(val)}
                    label={currentWorkspace?.name ?? "Chọn workspace"}
                    buttonClassName="!border-[0.5px] !border-subtle"
                    input
                  >
                    {workspaceIds.map((id) => {
                      const ws = getWorkspaceById(id);
                      return (
                        <CustomSelect.Option key={id} value={id}>
                          {ws?.name} ({ws?.slug})
                        </CustomSelect.Option>
                      );
                    })}
                  </CustomSelect>
                </div>
              </div>

              {currentWorkspace && (
                <div className="flex items-center gap-3">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleResendHandover}
                    loading={isActionLoading}
                    className="flex items-center gap-1.5"
                  >
                    <Send className="h-3.5 w-3.5" />
                    Gửi lại mật khẩu bàn giao
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleCreateBackup}
                    loading={isActionLoading}
                    className="flex items-center gap-1.5"
                  >
                    <Archive className="h-3.5 w-3.5" />
                    Tạo bản sao lưu ngay
                  </Button>
                </div>
              )}
            </div>

            {/* Backups List */}
            {isBackupsLoading ? (
              <Loader className="space-y-4 py-8">
                <Loader.Item height="40px" width="100%" />
                <Loader.Item height="60px" width="100%" />
                <Loader.Item height="60px" width="100%" />
              </Loader>
            ) : backups.length === 0 ? (
              <div className="rounded-lg border border-dashed border-subtle p-12 text-center">
                <Archive className="mx-auto h-10 w-10 text-placeholder" />
                <h4 className="text-15 mt-3 font-medium text-secondary">Chưa có bản sao lưu nào</h4>
                <p className="mt-1 text-13 text-tertiary">
                  Hệ thống tự động sao lưu lúc 02:00 hằng ngày (lưu 45 bản gần nhất). Bạn cũng có thể bấm &quot;Tạo bản
                  sao lưu ngay&quot;.
                </p>
              </div>
            ) : (
              <div className="overflow-hidden rounded-lg border border-subtle">
                <table className="w-full text-left text-13">
                  <thead className="border-b border-subtle bg-surface-2 text-12 font-medium text-tertiary">
                    <tr>
                      <th className="px-4 py-3">Tên Bản Sao Lưu / Thời Gian</th>
                      <th className="px-4 py-3">Loại Sao Lưu</th>
                      <th className="px-4 py-3">Số Bản Ghi</th>
                      <th className="px-4 py-3">Dung Lượng</th>
                      <th className="px-4 py-3 text-right">Thao Tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-subtle">
                    {backups.map((b: any) => {
                      const isAuto = b.backup_type === "auto";
                      const isPreDelete = b.backup_type === "pre-delete";
                      const isPreRestore = b.backup_type === "pre-restore";

                      return (
                        <tr key={b.backup_id} className="hover:bg-surface-1">
                          <td className="px-4 py-3">
                            <div className="font-mono font-medium text-primary">{b.filename}</div>
                            <div className="flex items-center gap-1 text-11 text-tertiary">
                              <Clock className="h-3 w-3" />
                              {new Date(b.created_at).toLocaleString("vi-VN")}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={cn(
                                "inline-flex items-center rounded-md px-2 py-0.5 text-11 font-medium",
                                isAuto
                                  ? "bg-blue-500/10 text-blue-500"
                                  : isPreDelete
                                    ? "bg-amber-500/10 text-amber-500"
                                    : isPreRestore
                                      ? "bg-purple-500/10 text-purple-500"
                                      : "bg-emerald-500/10 text-emerald-500"
                              )}
                            >
                              {isAuto
                                ? "Tự động (Hằng ngày)"
                                : isPreDelete
                                  ? "Trước khi xóa"
                                  : isPreRestore
                                    ? "Trước khi khôi phục"
                                    : "Thủ công"}
                            </span>
                          </td>
                          <td className="font-mono px-4 py-3 text-secondary">
                            {b.total_records?.toLocaleString()} bản ghi
                          </td>
                          <td className="font-mono px-4 py-3 text-secondary">{b.file_size_human}</td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <a
                                href={`/api/instances/workspaces/${selectedWorkspaceId}/backups/${b.backup_id}/`}
                                download
                                className={cn(getButtonStyling("secondary", "sm"), "flex items-center gap-1")}
                                title="Tải file về máy"
                              >
                                <Download className="h-3.5 w-3.5" />
                                Tải về
                              </a>
                              <Button
                                variant="error-fill"
                                size="sm"
                                onClick={() => setRestoreConfirmBackupId(b.backup_id)}
                                className="flex items-center gap-1"
                                title="Khôi phục workspace từ bản này"
                              >
                                <RotateCcw className="h-3.5 w-3.5" />
                                Khôi phục
                              </Button>
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => handleDeleteBackup(b.backup_id)}
                                className="text-danger-500 hover:text-danger-600"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* RESTORE CONFIRMATION MODAL */}
            {restoreConfirmBackupId && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                <div className="shadow-2xl w-full max-w-lg rounded-xl border border-subtle bg-surface-1 p-6">
                  <div className="text-danger-500 flex items-center gap-3">
                    <AlertTriangle className="h-6 w-6" />
                    <h3 className="text-16 font-semibold">Xác nhận khôi phục Workspace độc lập</h3>
                  </div>

                  <p className="mt-3 text-13 leading-relaxed text-secondary">
                    Hệ thống sẽ thay thế dữ liệu của workspace <strong>{currentWorkspace?.name}</strong> bằng dữ liệu từ
                    bản sao lưu{" "}
                    <code className="font-mono rounded bg-surface-2 px-1 py-0.5 text-12">{restoreConfirmBackupId}</code>
                    .
                  </p>
                  <p className="mt-2 text-12 text-tertiary">
                    (Một bản sao lưu phòng ngừa <code className="text-11">pre-restore</code> sẽ được tạo tự động. Các
                    workspace khác và hệ thống Civix không bị ảnh hưởng).
                  </p>

                  <div className="mt-4 space-y-1">
                    <label className="text-12 font-medium text-secondary">
                      Nhập slug của workspace{" "}
                      <code className="text-danger-500 font-bold">{currentWorkspace?.slug}</code> để xác nhận:
                    </label>
                    <Input
                      type="text"
                      value={restoreConfirmationInput}
                      onChange={(e) => setRestoreConfirmationInput(e.target.value)}
                      placeholder={currentWorkspace?.slug}
                      className="w-full"
                    />
                  </div>

                  <div className="mt-6 flex justify-end gap-3">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setRestoreConfirmBackupId(null);
                        setRestoreConfirmationInput("");
                      }}
                    >
                      Hủy bỏ
                    </Button>
                    <Button
                      variant="error-fill"
                      size="sm"
                      onClick={handleExecuteRestore}
                      loading={isActionLoading}
                      disabled={restoreConfirmationInput !== currentWorkspace?.slug}
                    >
                      Xác nhận khôi phục
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: TRASH (15 DAYS) */}
        {activeTab === "trash" && (
          <div className="space-y-4">
            <div className="bg-amber-500/10 text-amber-500 border-amber-500/20 flex items-center gap-2 rounded-md border p-3 text-12">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>
                Các Workspace bị xóa sẽ được lưu trữ tạm thời trong <strong>15 ngày</strong>. Quản trị viên God-mode có
                thể khôi phục lại bất kỳ lúc nào trước khi hệ thống tự động dọn dẹp vĩnh viễn.
              </span>
            </div>

            {isTrashLoading ? (
              <Loader className="space-y-4 py-8">
                <Loader.Item height="50px" width="100%" />
                <Loader.Item height="50px" width="100%" />
              </Loader>
            ) : trashItems.length === 0 ? (
              <div className="rounded-lg border border-dashed border-subtle p-12 text-center">
                <ShieldCheck className="text-emerald-500 mx-auto h-10 w-10" />
                <h4 className="text-15 mt-3 font-medium text-secondary">Thùng rác đang trống</h4>
                <p className="mt-1 text-13 text-tertiary">Không có workspace nào đang trong thời gian chờ xóa.</p>
              </div>
            ) : (
              <div className="overflow-hidden rounded-lg border border-subtle">
                <table className="w-full text-left text-13">
                  <thead className="border-b border-subtle bg-surface-2 text-12 font-medium text-tertiary">
                    <tr>
                      <th className="px-4 py-3">Tên Workspace</th>
                      <th className="px-4 py-3">Slug</th>
                      <th className="px-4 py-3">Chủ sở hữu</th>
                      <th className="px-4 py-3">Ngày Xóa</th>
                      <th className="px-4 py-3">Hạn Còn Lại</th>
                      <th className="px-4 py-3 text-right">Thao Tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-subtle">
                    {trashItems.map((ws: any) => (
                      <tr key={ws.id} className="hover:bg-surface-1">
                        <td className="px-4 py-3 font-medium text-primary">{ws.name}</td>
                        <td className="font-mono px-4 py-3 text-tertiary">{ws.slug}</td>
                        <td className="px-4 py-3 text-secondary">{ws.owner_email || "Chưa có"}</td>
                        <td className="px-4 py-3 text-tertiary">
                          {new Date(ws.deleted_at).toLocaleDateString("vi-VN")}
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-danger-500 inline-flex items-center gap-1 font-semibold">
                            <Clock className="h-3.5 w-3.5" />
                            {ws.days_remaining} ngày
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => handleRestoreTrashWorkspace(ws.id, ws.name)}
                              className="flex items-center gap-1"
                            >
                              <RotateCcw className="h-3.5 w-3.5" />
                              Khôi phục
                            </Button>
                            <Button
                              variant="error-fill"
                              size="sm"
                              onClick={() => handlePurgeWorkspace(ws.id, ws.slug)}
                              className="flex items-center gap-1"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                              Xóa vĩnh viễn
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </PageWrapper>
  );
});

export default WorkspaceBackupsPage;
