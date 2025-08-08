import React from 'react';

interface PatientInfoProps {
  data: {
    nhs?: string;
    hospitalNumber?: string;
    nsNumber?: string;
    name?: string;
    coder?: string;
    consent?: string;
    dateOfBiopsy?: string;
  };
  onChange: (data: any) => void;
}

const PatientInfo: React.FC<PatientInfoProps> = ({ data, onChange }) => {
  const handleChange = (field: string, value: string) => {
    onChange({ ...data, [field]: value });
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Patient Information</h2>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            NHS Number
          </label>
          <input
            type="text"
            value={data.nhs || ''}
            onChange={(e) => handleChange('nhs', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="123 4567 8901"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Hospital Number
          </label>
          <input
            type="text"
            value={data.hospitalNumber || ''}
            onChange={(e) => handleChange('hospitalNumber', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="31098674"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            NS Number
          </label>
          <input
            type="text"
            value={data.nsNumber || ''}
            onChange={(e) => handleChange('nsNumber', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="25-67890"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Name
          </label>
          <input
            type="text"
            value={data.name || ''}
            onChange={(e) => handleChange('name', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Smith"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Coder
          </label>
          <select
            value={data.coder || ''}
            onChange={(e) => handleChange('coder', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select...</option>
            <option value="CR">CR</option>
            <option value="AS">AS</option>
            <option value="NS">NS</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Consent
          </label>
          <select
            value={data.consent || ''}
            onChange={(e) => handleChange('consent', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select...</option>
            <option value="PISv.8">PISv.8</option>
            <option value="TB">TB</option>
            <option value="U">U</option>
          </select>
        </div>
        
        <div className="col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Date of Biopsy
          </label>
          <input
            type="text"
            value={data.dateOfBiopsy || ''}
            onChange={(e) => handleChange('dateOfBiopsy', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="dd/mm/yyyy"
          />
        </div>
      </div>
    </div>
  );
};

export default PatientInfo;