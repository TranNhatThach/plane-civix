/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import { KeyRound, ShieldAlert } from "lucide-react";
import { Button } from "@plane/propel/button";
import { useCommandPalette } from "@/hooks/store/use-command-palette";
import { useUser } from "@/hooks/store/user";

export const MustChangePasswordBanner = observer(function MustChangePasswordBanner() {
  const { data: currentUser } = useUser();
  const { toggleProfileSettingsModal } = useCommandPalette();

  if (!currentUser?.must_change_password) {
    return null;
  }

  return (
    <div className="border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300 flex w-full items-center justify-between border-b px-4 py-2 text-13">
      <div className="flex items-center gap-2">
        <ShieldAlert className="text-amber-500 h-4 w-4 shrink-0" />
        <span>
          <strong>Lưu ý bảo mật:</strong> Bạn đang đăng nhập bằng mật khẩu tạm thời. Vui lòng đổi mật khẩu mới để bảo vệ
          tài khoản và mở khóa đầy đủ tính năng.
        </span>
      </div>
      <Button
        variant="primary"
        size="sm"
        className="bg-amber-600 hover:bg-amber-700 ml-4 shrink-0 border-none text-white"
        onClick={() => toggleProfileSettingsModal({ isOpen: true, activeTab: "security" })}
      >
        <KeyRound className="mr-1.5 h-3.5 w-3.5" />
        Đổi mật khẩu ngay
      </Button>
    </div>
  );
});
