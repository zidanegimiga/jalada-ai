import { Spinner } from "@/shared/components/Spinner";

/** Shown while a page's first data loads during navigation. */
export default function Loading() {
  return (
    <main className="mx-auto flex w-full max-w-page flex-1 flex-col justify-center px-gutter">
      <Spinner label="Loading the page" />
    </main>
  );
}
