import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Remove rendered components after each test so tests cannot see each other's output.
afterEach(cleanup);
