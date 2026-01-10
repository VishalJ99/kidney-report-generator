import React from 'react';

interface ConclusionCode {
  key: string;
  code: string;
}

interface ConclusionCodesProps {
  codes: ConclusionCode[];
}

const ConclusionCodes: React.FC<ConclusionCodesProps> = ({ codes }) => {
  if (!codes || codes.length === 0) return null;

  return (
    <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <h3 className="font-semibold text-gray-800 mb-3">
        Extracted Conclusion Codes
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {codes.map(({ key, code }, idx) => (
          <div
            key={`${key}-${idx}`}
            className="flex justify-between items-center bg-white px-3 py-2 rounded border border-gray-100"
          >
            <span className="font-mono text-sm text-gray-700">{key}</span>
            <span className="text-sm text-gray-600 truncate ml-2" title={code}>
              {code.length > 40 ? code.substring(0, 40) + '...' : code}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ConclusionCodes;
