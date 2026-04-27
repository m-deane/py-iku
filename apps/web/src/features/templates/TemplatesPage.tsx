/**
 * Templates is a Sprint-3 module — empty placeholder route for now.
 * The IA review proposed it as the third Library cluster item alongside
 * Catalog and Snippets, so we expose the destination so navigation feels
 * complete even before the gallery lands.
 */
export function TemplatesPage(): JSX.Element {
  return (
    <section
      style={{
        padding: "var(--space-6, 32px)",
        maxWidth: 720,
        margin: "0 auto",
      }}
    >
      <h1 style={{ marginTop: 0 }}>Templates</h1>
      <p style={{ color: "var(--fg-muted, #5b6470)", marginTop: 0 }}>
        Reusable starter flows that combine a script, snippet pre-fills, and
        recipe shape — coming in Sprint 3. For now, browse{" "}
        <a href="/snippets">Snippets</a> for individual building blocks.
      </p>
    </section>
  );
}
