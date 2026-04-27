import type { ParameterSpec } from "./templates-data";

export interface ParameterFormProps {
  parameters: ParameterSpec[];
  values: Record<string, string>;
  onChange: (name: string, value: string) => void;
}

/**
 * Render an input control per ``ParameterSpec``. Plain HTML inputs styled
 * via ``ui-tokens.css`` — no external form library so the parametric flow
 * works in the same render tree as the rest of the templates page.
 *
 * The parent owns the values dict; this component is fully controlled.
 */
export function ParameterForm(props: ParameterFormProps): JSX.Element {
  const { parameters, values, onChange } = props;
  return (
    <div
      data-testid="template-parameter-form"
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "var(--space-3, 12px)",
      }}
    >
      {parameters.map((spec) => (
        <ParameterField
          key={spec.name}
          spec={spec}
          value={values[spec.name] ?? spec.defaultValue}
          onChange={(v) => onChange(spec.name, v)}
        />
      ))}
    </div>
  );
}

interface ParameterFieldProps {
  spec: ParameterSpec;
  value: string;
  onChange: (next: string) => void;
}

function ParameterField({ spec, value, onChange }: ParameterFieldProps): JSX.Element {
  const inputId = `param-${spec.name}`;
  const inputStyle: React.CSSProperties = {
    padding: "var(--space-2, 6px) var(--space-3, 8px)",
    border: "1px solid var(--border, #eaecf0)",
    borderRadius: "var(--radius-md, 6px)",
    fontSize: "var(--text-sm, 14px)",
    background: "var(--surface, #ffffff)",
    color: "var(--fg, #101828)",
  };

  const renderControl = (): JSX.Element => {
    switch (spec.type) {
      case "select":
        return (
          <select
            id={inputId}
            data-testid={`param-input-${spec.name}`}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            style={inputStyle}
          >
            {(spec.choices ?? []).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        );
      case "number":
        return (
          <input
            id={inputId}
            data-testid={`param-input-${spec.name}`}
            type="number"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            style={inputStyle}
          />
        );
      case "date":
        return (
          <input
            id={inputId}
            data-testid={`param-input-${spec.name}`}
            type="date"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            style={inputStyle}
          />
        );
      case "text":
      default:
        return (
          <input
            id={inputId}
            data-testid={`param-input-${spec.name}`}
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            style={inputStyle}
          />
        );
    }
  };

  return (
    <label
      htmlFor={inputId}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 4,
        fontSize: "var(--text-xs, 12px)",
      }}
    >
      <span style={{ color: "var(--fg-muted, #5b6470)", fontWeight: 600 }}>
        {spec.label}
        <code
          style={{
            marginLeft: 6,
            fontFamily: "var(--font-mono, monospace)",
            fontSize: 11,
            color: "var(--fg-muted, #5b6470)",
            fontWeight: 400,
          }}
        >
          ${"{" + spec.name + "}"}
        </code>
      </span>
      {renderControl()}
      {spec.description ? (
        <span
          style={{
            color: "var(--fg-muted, #5b6470)",
            fontSize: "var(--text-xs, 11px)",
          }}
        >
          {spec.description}
        </span>
      ) : null}
    </label>
  );
}
