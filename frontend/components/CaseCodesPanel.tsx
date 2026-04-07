'use client';

interface CaseCode {
  key: string;
  section: string;
  label: string;
  codes: Record<string, string>;
}

interface CaseCodesPanelProps {
  codes: CaseCode[];
  reportType: 'transplant' | 'native';
}

const CODE_PRIORITY: Record<'transplant' | 'native', string[]> = {
  transplant: ['transplant', 'native1', 'kbc'],
  native: ['native1', 'kbc', 'transplant'],
};

const formatCodeLabel = (codeType: string) => codeType.replace(/_/g, ' ').toUpperCase();

export default function CaseCodesPanel({ codes, reportType }: CaseCodesPanelProps) {
  const preferredOrder = CODE_PRIORITY[reportType];

  const sortCodes = (entries: [string, string][]) => {
    return [...entries].sort(([left], [right]) => {
      const leftIndex = preferredOrder.indexOf(left);
      const rightIndex = preferredOrder.indexOf(right);
      const normalizedLeft = leftIndex === -1 ? preferredOrder.length : leftIndex;
      const normalizedRight = rightIndex === -1 ? preferredOrder.length : rightIndex;

      if (normalizedLeft !== normalizedRight) {
        return normalizedLeft - normalizedRight;
      }

      return left.localeCompare(right);
    });
  };

  return (
    <div className="rounded-lg bg-white p-6 shadow">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Case codes</h2>
        <p className="mt-1 text-sm text-gray-500">
          Codes are collected from completed shorthand tokens as you type. The current report type is emphasized, but all available code families remain visible.
        </p>
      </div>

      {codes.length === 0 ? (
        <div className="rounded border border-dashed border-gray-300 bg-gray-50 px-4 py-6 text-sm text-gray-500">
          No code-bearing shorthand has been completed yet.
        </div>
      ) : (
        <div className="space-y-3">
          {codes.map((entry) => (
            <div key={entry.key} className="rounded border border-gray-200 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-gray-900">{entry.key}</div>
                  <div className="mt-1 text-sm text-gray-600">{entry.label}</div>
                </div>
                <span className="rounded bg-gray-100 px-2 py-1 text-xs font-medium uppercase tracking-wide text-gray-600">
                  {entry.section}
                </span>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                {sortCodes(Object.entries(entry.codes)).map(([codeType, codeValue]) => {
                  const isPreferred = preferredOrder[0] === codeType;
                  return (
                    <div
                      key={`${entry.key}-${codeType}`}
                      className={isPreferred
                        ? 'rounded border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-900'
                        : 'rounded border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-700'}
                    >
                      <span className="font-medium">{formatCodeLabel(codeType)}:</span> {codeValue}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
