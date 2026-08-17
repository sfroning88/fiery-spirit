import { PropertyListSkeleton } from "@/app/(components)/(properties)/PropertyListSkeleton";

export default function HomeLoading() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1 animate-pulse">
        <div className="h-8 w-36 rounded bg-zinc-200" />
        <div className="h-4 w-52 rounded bg-zinc-100 mt-1" />
      </div>
      <PropertyListSkeleton />
    </div>
  );
}
