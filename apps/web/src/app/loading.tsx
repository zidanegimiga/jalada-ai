import { Spinner } from "@/components/ui/spinner";

/** Shown while a page's first data loads during navigation. */
export default function Loading() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-4">
      <Spinner label="Loading the page" />
    </main>
  );
}
