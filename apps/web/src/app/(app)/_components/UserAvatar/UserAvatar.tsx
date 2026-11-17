import Link from "next/link";

import { getCurrentUser } from "@/features/auth/server/get-current-user";
import { Avatar } from "@/shared/components/Avatar";

/** The signed-in person's avatar, linking to their account. */
export async function UserAvatar() {
  const user = await getCurrentUser();
  const name = user?.display_name ?? "";
  return (
    <Link
      href="/account"
      className="rounded-full transition-transform active:scale-95"
    >
      <Avatar name={name} />
      <span className="sr-only">
        {name ? `Account for ${name}` : "Account"}
      </span>
    </Link>
  );
}
