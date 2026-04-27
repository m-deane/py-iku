import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Breadcrumb } from "../../src/components/Breadcrumb";
import { RouteBreadcrumb } from "../../src/components/RouteBreadcrumb";

describe("<Breadcrumb />", () => {
  it("renders an accessible navigation landmark", () => {
    render(
      <MemoryRouter>
        <Breadcrumb items={[{ label: "Lifecycle" }, { label: "Diff" }]} />
      </MemoryRouter>,
    );
    const nav = screen.getByRole("navigation", { name: /breadcrumb/i });
    expect(nav).toBeInTheDocument();
  });

  it("marks the last crumb with aria-current=page", () => {
    render(
      <MemoryRouter>
        <Breadcrumb items={[{ label: "Build" }, { label: "Convert" }]} />
      </MemoryRouter>,
    );
    const current = screen.getByText("Convert").closest("li");
    expect(current).toHaveAttribute("aria-current", "page");
  });

  it("returns nothing for an empty list", () => {
    const { container } = render(
      <MemoryRouter>
        <Breadcrumb items={[]} />
      </MemoryRouter>,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders intermediate crumbs as links when `to` is provided", () => {
    render(
      <MemoryRouter>
        <Breadcrumb
          items={[
            { label: "Lifecycle", to: "/lifecycle" },
            { label: "Audit" },
          ]}
        />
      </MemoryRouter>,
    );
    const link = screen.getByRole("link", { name: "Lifecycle" });
    expect(link).toHaveAttribute("href", "/lifecycle");
  });
});

describe("<RouteBreadcrumb />", () => {
  it("renders 'Lifecycle / Diff' for /diff", () => {
    render(
      <MemoryRouter initialEntries={["/diff"]}>
        <RouteBreadcrumb />
      </MemoryRouter>,
    );
    expect(screen.getByText("Lifecycle")).toBeInTheDocument();
    expect(screen.getByText("Diff")).toBeInTheDocument();
  });

  it("renders 'Build / Convert' for /convert", () => {
    render(
      <MemoryRouter initialEntries={["/convert"]}>
        <RouteBreadcrumb />
      </MemoryRouter>,
    );
    expect(screen.getByText("Build")).toBeInTheDocument();
    expect(screen.getByText("Convert")).toBeInTheDocument();
  });

  it("renders 'Account / Settings' for /settings", () => {
    render(
      <MemoryRouter initialEntries={["/settings"]}>
        <RouteBreadcrumb />
      </MemoryRouter>,
    );
    expect(screen.getByText("Account")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("renders nothing on the home route", () => {
    const { container } = render(
      <MemoryRouter initialEntries={["/"]}>
        <RouteBreadcrumb />
      </MemoryRouter>,
    );
    expect(container.firstChild).toBeNull();
  });
});
