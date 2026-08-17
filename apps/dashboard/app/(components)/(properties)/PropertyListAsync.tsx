import { use } from "react";
import type { PropertyListEntry } from "@focus/types";
import { PropertyList } from "./PropertyList";

type PropertyListAsyncProps = {
  initialDataPromise: Promise<PropertyListEntry[]>;
};

export function PropertyListAsync({
  initialDataPromise,
}: PropertyListAsyncProps) {
  const initialData = use(initialDataPromise);
  return <PropertyList initialData={initialData} />;
}
