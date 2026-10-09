/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { useSearchParams } from "next/navigation";
import useSWR from "swr";
import { AlertTriangle, Boxes, LogOut, Share2, Star, User2 } from "lucide-react";
import { CheckIcon, CloseIcon } from "@plane/propel/icons";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
// components
import { LogoSpinner } from "@/components/common/logo-spinner";
import { EmptySpace, EmptySpaceItem } from "@/components/ui/empty-space";
// constants
import { WORKSPACE_INVITATION } from "@plane/constants";
// helpers
import { EPageTypes } from "@/helpers/authentication.helper";
// hooks
import { useUser } from "@/hooks/store/user";
import { useAppRouter } from "@/hooks/use-app-router";
// wrappers
import { AuthenticationWrapper } from "@/lib/wrappers/authentication-wrapper";
import { WorkspaceService } from "@/services/workspace.service";
// services

// service initialization
const workspaceService = new WorkspaceService();

function WorkspaceInvitationPage() {
  // router
  const router = useAppRouter();
  // states
  const [isSubmitting, setIsSubmitting] = useState(false);
  // query params
  const searchParams = useSearchParams();
  const invitation_id = searchParams.get("invitation_id");
  const slug = searchParams.get("slug");
  const token = searchParams.get("token");
  // normalize slug to prevent issues with spaces
  const normalizedSlug = slug
    ? slug
        .toString()
        .trim()
        .replace(/%20|\s+/g, "-")
    : "";
  // store hooks
  const { data: currentUser, signOut } = useUser();

  const { data: invitationDetail, error } = useSWR(
    invitation_id && normalizedSlug && WORKSPACE_INVITATION(invitation_id.toString()),
    invitation_id && normalizedSlug
      ? () => workspaceService.getWorkspaceInvitation(normalizedSlug, invitation_id.toString())
      : null
  );

  const currentEmail = currentUser?.email ? currentUser.email.trim().toLowerCase() : "";
  const invitedEmail = invitationDetail?.email ? invitationDetail.email.trim().toLowerCase() : "";

  const isUserAuthenticated = Boolean(currentEmail);
  const isEmailMismatch = Boolean(isUserAuthenticated && invitedEmail && currentEmail !== invitedEmail);

  const handleGoToSignIn = () => {
    const currentUrl = typeof window !== "undefined" ? window.location.pathname + window.location.search : "";
    router.push(
      `/?email=${encodeURIComponent(invitationDetail?.email || "")}&next_path=${encodeURIComponent(currentUrl)}`
    );
  };

  const handleSignOutAndSwitch = async () => {
    setIsSubmitting(true);
    try {
      await signOut();
      const currentUrl = typeof window !== "undefined" ? window.location.pathname + window.location.search : "";
      router.push(
        `/?email=${encodeURIComponent(invitationDetail?.email || "")}&next_path=${encodeURIComponent(currentUrl)}`
      );
    } catch (err) {
      console.error(err);
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Lỗi đăng xuất",
        message: "Không thể đăng xuất phiên làm việc hiện tại.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAccept = async () => {
    if (!invitationDetail) return;

    if (!isUserAuthenticated) {
      handleGoToSignIn();
      return;
    }

    if (isEmailMismatch) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Tài khoản không khớp",
        message: `Bạn đang đăng nhập bằng ${currentUser?.email}. Vui lòng đăng xuất và đăng nhập bằng ${invitationDetail.email} để chấp nhận lời mời.`,
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await workspaceService.joinWorkspace(invitationDetail.workspace.slug, invitationDetail.id, {
        accepted: true,
        token: token,
      });
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Thành công",
        message: `Chào mừng bạn đến với workspace ${invitationDetail.workspace.name}!`,
      });
      if (invitationDetail.email === currentUser?.email) {
        router.push(`/${invitationDetail.workspace.slug}`);
      } else {
        router.push("/");
      }
    } catch (err: any) {
      console.error(err);
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Lỗi tham gia workspace",
        message: err?.error || err?.message || "Không thể tham gia workspace. Vui lòng thử lại.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!invitationDetail || !token) return;
    setIsSubmitting(true);
    try {
      await workspaceService.joinWorkspace(invitationDetail.workspace.slug, invitationDetail.id, {
        accepted: false,
        token: token,
      });
      setToast({
        type: TOAST_TYPE.INFO,
        title: "Đã từ chối",
        message: "Bạn đã từ chối lời mời tham gia workspace.",
      });
      router.push("/");
    } catch (err: any) {
      console.error(err);
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Lỗi",
        message: err?.error || err?.message || "Không thể từ chối lời mời. Vui lòng thử lại.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthenticationWrapper pageType={EPageTypes.PUBLIC}>
      <div className="flex h-full w-full flex-col items-center justify-center px-3">
        {invitationDetail && !invitationDetail.responded_at ? (
          error ? (
            <div className="shadow-2xl flex w-full flex-col space-y-4 rounded-sm border border-subtle bg-surface-1 px-4 py-8 text-center md:w-1/3">
              <h2 className="text-18 uppercase">INVITATION NOT FOUND</h2>
            </div>
          ) : (
            <div className="flex w-full flex-col items-center">
              {isEmailMismatch && (
                <div className="border-amber-500/30 bg-amber-500/10 mb-6 w-full max-w-lg rounded-lg border p-4 text-left">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="text-amber-500 mt-0.5 h-5 w-5 flex-shrink-0" />
                    <div className="space-y-1 text-13">
                      <p className="text-amber-500 font-semibold">Tài khoản hiện tại không khớp với lời mời</p>
                      <p className="text-secondary">
                        Bạn đang đăng nhập bằng{" "}
                        <strong className="font-medium text-primary">{currentUser?.email}</strong>, nhưng lời mời này
                        được gửi riêng cho{" "}
                        <strong className="font-medium text-primary">{invitationDetail.email}</strong>.
                      </p>
                      <p className="text-12 text-tertiary">
                        Vui lòng chuyển sang tài khoản <span className="font-medium">{invitationDetail.email}</span>{" "}
                        hoặc mở liên kết trong cửa sổ ẩn danh (Incognito) để tham gia.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {!isUserAuthenticated && (
                <div className="border-blue-500/30 bg-blue-500/10 mb-6 w-full max-w-lg rounded-lg border p-4 text-left">
                  <div className="flex items-start gap-3">
                    <User2 className="text-blue-500 mt-0.5 h-5 w-5 flex-shrink-0" />
                    <div className="space-y-1 text-13">
                      <p className="text-blue-500 font-semibold">Yêu cầu xác thực tài khoản</p>
                      <p className="text-secondary">
                        Lời mời tham gia workspace này được gửi riêng tới{" "}
                        <strong className="font-medium text-primary">{invitationDetail.email}</strong>.
                      </p>
                      <p className="text-12 text-tertiary">
                        Vui lòng nhấp vào nút bên dưới để đăng nhập hoặc tạo tài khoản mới và tự động kích hoạt tư cách
                        thành viên.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <EmptySpace
                title={`You have been invited to ${invitationDetail.workspace.name}`}
                description="Your workspace is where you'll create projects, collaborate on your work items, and organize different streams of work in your Plane account."
              >
                {isEmailMismatch ? (
                  <>
                    <EmptySpaceItem
                      Icon={LogOut}
                      title={isSubmitting ? "Đang xử lý..." : `Đăng xuất và đăng nhập bằng ${invitationDetail.email}`}
                      description={`Chuyển sang tài khoản ${invitationDetail.email} để chấp nhận lời mời`}
                      action={isSubmitting ? undefined : handleSignOutAndSwitch}
                    />
                    <EmptySpaceItem
                      Icon={Boxes}
                      title={`Tiếp tục với tài khoản ${currentUser?.email}`}
                      description="Quay lại trang chính"
                      href="/"
                    />
                  </>
                ) : !isUserAuthenticated ? (
                  <>
                    <EmptySpaceItem
                      Icon={CheckIcon}
                      title={
                        isSubmitting
                          ? "Đang xử lý..."
                          : `Đăng nhập / Đăng ký bằng ${invitationDetail.email} để tham gia`
                      }
                      description="Xác thực tài khoản để tự động chấp nhận lời mời"
                      action={handleGoToSignIn}
                    />
                    <EmptySpaceItem Icon={CloseIcon} title="Ignore" action={handleReject} />
                  </>
                ) : (
                  <>
                    <EmptySpaceItem
                      Icon={CheckIcon}
                      title={isSubmitting ? "Đang tham gia..." : "Accept"}
                      action={isSubmitting ? undefined : handleAccept}
                    />
                    <EmptySpaceItem
                      Icon={CloseIcon}
                      title={isSubmitting ? "Đang xử lý..." : "Ignore"}
                      action={isSubmitting ? undefined : handleReject}
                    />
                  </>
                )}
              </EmptySpace>
            </div>
          )
        ) : error || invitationDetail?.responded_at ? (
          invitationDetail?.accepted ? (
            <EmptySpace
              title={`You are already a member of ${invitationDetail.workspace.name}`}
              description="Your workspace is where you'll create projects, collaborate on your work items, and organize different streams of work in your Plane account."
            >
              <EmptySpaceItem Icon={Boxes} title="Continue to home" href="/" />
            </EmptySpace>
          ) : (
            <EmptySpace
              title="This invitation link is not active anymore."
              description="Your workspace is where you'll create projects, collaborate on your work items, and organize different streams of work in your Plane account."
              link={{ text: "Or start from an empty project", href: "/" }}
            >
              {!currentUser ? (
                <EmptySpaceItem Icon={User2} title="Sign in to continue" href="/" />
              ) : (
                <EmptySpaceItem Icon={Boxes} title="Continue to home" href="/" />
              )}
              <EmptySpaceItem Icon={Star} title="Star us on GitHub" href="https://github.com/makeplane" />
              <EmptySpaceItem
                Icon={Share2}
                title="Join our community of active creators"
                href="https://forum.plane.so"
              />
            </EmptySpace>
          )
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <LogoSpinner />
          </div>
        )}
      </div>
    </AuthenticationWrapper>
  );
}

export default observer(WorkspaceInvitationPage);
