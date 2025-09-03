import React from 'react';

interface ShorthandInputProps {
  value: string;
  onChange: (value: string) => void;
  onLoadExample: () => void;
}

const ShorthandInput: React.FC<ShorthandInputProps> = ({ value, onChange, onLoadExample }) => {
  const sections = [
    { key: 'Patient', hint: 'NHS, HN, NS, Name, Coder, Consent, Date' },
    { key: 'LM', hint: 'Light Microscopy: CM, C2M1, etc.' },
    { key: 'Glom', hint: 'Glomeruli: 31, Gs7, Ss1_NOS, Mm1, Mc1, G2, Cg1' },
    { key: 'TI', hint: 'Tubulointerstitium: ATI_micro, IFTA20, T1, etc.' },
    { key: 'Ves', hint: 'Blood Vessels: A3, 2IL_1Ar, Cv2, V0, Ah1, Ptc1' },
    { key: 'IHC', hint: 'Immunohistochemistry: C4d0, SV40_0' },
    { key: 'EM', hint: 'Electron Microscopy: EM0, EM1' },
    { key: 'IFFR', hint: 'Immunofluorescence: FR_0, FR0' },
    { key: 'CONCLUSION', hint: 'BL, MVI+, MildIFTA, etc.' },
    { key: 'COMMENT', hint: 'MVI+, DP, NR, etc.' },
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold">Shorthand Entry</h2>
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
            Press TAB for reference
          </span>
        </div>
        <button
          onClick={onLoadExample}
          className="text-sm text-blue-600 hover:text-blue-700 underline"
        >
          Load Example
        </button>
      </div>
      
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full h-96 px-4 py-3 border border-gray-300 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        placeholder="Enter shorthand notation here...

Example:
NHS: 234 4567 2345
HN: 31098674
NS: 25-67890
Name: Smith
Coder: CR
Consent: PISv.8
Date of biopsy: 12/07/2025
LM: CM, C2M1
Glom: 31, Gs7, Ss1_NOS
..."
      />
      
      <div className="mt-4 space-y-2">
        <p className="text-sm font-medium text-gray-700">Quick Reference:</p>
        <div className="grid grid-cols-2 gap-2 text-xs">
          {sections.map((section) => (
            <div key={section.key} className="bg-gray-50 p-2 rounded">
              <span className="font-semibold text-gray-900">{section.key}:</span>{' '}
              <span className="text-gray-600">{section.hint}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ShorthandInput;