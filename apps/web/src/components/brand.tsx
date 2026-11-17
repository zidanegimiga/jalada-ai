import Image from "next/image";

/** The logo and the name, at the top of every page. */
export function Brand() {
  return (
    <p className="flex items-center gap-2 text-lead font-bold">
      <Image
        src="/mark.webp"
        alt=""
        width={40}
        height={40}
        unoptimized
        className="size-10 rounded-control"
      />
      Jalada AI
    </p>
  );
}
