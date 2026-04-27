/**
 * Sprint-6 — dataset-stripe family resolution.
 */
import { describe, expect, it } from "vitest";
import {
  datasetStripeColor,
  familyFor,
  KNOWN_CONNECTION_TYPES,
} from "../src/icons/datasetStripe";

describe("datasetStripeColor", () => {
  it("returns a CSS variable expression", () => {
    expect(datasetStripeColor("Filesystem")).toMatch(/^var\(--dataset-stripe-/);
    expect(datasetStripeColor("PostgreSQL")).toMatch(/^var\(--dataset-stripe-/);
  });

  it("maps SQL connection variants to the SQL stripe", () => {
    for (const t of [
      "PostgreSQL",
      "MySQL",
      "BigQuery",
      "Snowflake",
      "Redshift",
      "SQL_POSTGRESQL",
      "SQL_MYSQL",
    ]) {
      expect(familyFor(t), t).toBe("sql");
    }
  });

  it("maps cloud object stores to the cloud stripe", () => {
    for (const t of ["S3", "GCS", "Azure", "AZURE_BLOB", "HDFS"]) {
      expect(familyFor(t), t).toBe("cloud");
    }
  });

  it("maps NoSQL connections to the nosql stripe", () => {
    expect(familyFor("MongoDB")).toBe("nosql");
  });

  it("maps Filesystem and ManagedFolder to the filesystem stripe", () => {
    expect(familyFor("Filesystem")).toBe("filesystem");
    expect(familyFor("ManagedFolder")).toBe("filesystem");
  });

  it("falls back to the default stripe for unknown connection types", () => {
    expect(familyFor("Unknown")).toBe("default");
    expect(datasetStripeColor("Unknown")).toBe("var(--dataset-stripe-default)");
  });

  it("ships ≥ 12 known connection-type aliases", () => {
    expect(KNOWN_CONNECTION_TYPES.length).toBeGreaterThanOrEqual(12);
  });
});
