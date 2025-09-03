import React, { useState, useMemo } from 'react';

interface MappingReferenceProps {
  isOpen: boolean;
  mappings: Record<string, string>;
}

const MappingReference: React.FC<MappingReferenceProps> = ({ isOpen, mappings }) => {
  const [searchTerm, setSearchTerm] = useState('');

  // Categorize mappings
  const categorizedMappings = useMemo(() => {
    const categories: Record<string, Array<[string, string]>> = {
      'Headers': [],
      'Sample Description': [],
      'Glomeruli': [],
      'Tubulointerstitium': [],
      'Blood Vessels': [],
      'Immunohistochemistry': [],
      'Electron Microscopy': [],
      'Immunofluorescence': [],
      'Conclusion': [],
      'Comment': [],
      'Other': []
    };

    Object.entries(mappings).forEach(([key, value]) => {
      // Skip regex patterns for now (starting with ~)
      const displayKey = key.startsWith('~') ? key.substring(1) + ' (pattern)' : key;
      
      // Categorize based on key patterns
      if (key.startsWith('!')) {
        categories['Headers'].push([displayKey, value]);
      } else if (key.match(/^(C|M|CT|CM|CCT|MCT|CMCT|~C\d)/)) {
        categories['Sample Description'].push([displayKey, value]);
      } else if (key.match(/(^TG|^GS|^SS|^MM\d|^MC\d|^ISCH|^G\d|^CG\d|^FN|^CC)/)) {
        categories['Glomeruli'].push([displayKey, value]);
      } else if (key.match(/(^ATI|^IFTA|^T\d|^I\d|^TI\d|^CTCI)/)) {
        categories['Tubulointerstitium'].push([displayKey, value]);
      } else if (key.match(/(^A\d|^CV\d|^V\d|^AH\d|^PTC\d|^CAA|IL|Ar)/)) {
        categories['Blood Vessels'].push([displayKey, value]);
      } else if (key.match(/(^C4D|^SV40)/)) {
        categories['Immunohistochemistry'].push([displayKey, value]);
      } else if (key.match(/^EM/)) {
        categories['Electron Microscopy'].push([displayKey, value]);
      } else if (key.match(/(^FR|^IFFR|^IF)/)) {
        categories['Immunofluorescence'].push([displayKey, value]);
      } else if (key.match(/(^BL|^TCMR|^MVI|^AMR|IFTA$)/)) {
        categories['Conclusion'].push([displayKey, value]);
      } else if (key.match(/(^NR|^DP|^FSGS|^TMA)/)) {
        categories['Comment'].push([displayKey, value]);
      } else {
        categories['Other'].push([displayKey, value]);
      }
    });

    // Remove empty categories
    Object.keys(categories).forEach(cat => {
      if (categories[cat].length === 0) {
        delete categories[cat];
      }
    });

    return categories;
  }, [mappings]);

  // Filter mappings based on search
  const filteredCategories = useMemo(() => {
    if (!searchTerm) return categorizedMappings;

    const filtered: Record<string, Array<[string, string]>> = {};
    const searchLower = searchTerm.toLowerCase();

    Object.entries(categorizedMappings).forEach(([category, items]) => {
      const filteredItems = items.filter(([key, value]) => 
        key.toLowerCase().includes(searchLower) || 
        value.toLowerCase().includes(searchLower)
      );
      if (filteredItems.length > 0) {
        filtered[category] = filteredItems;
      }
    });

    return filtered;
  }, [categorizedMappings, searchTerm]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-2xl w-[90%] max-w-6xl h-[85vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-bold text-gray-900">
              Shorthand Reference Guide
            </h2>
            <span className="text-sm text-gray-500">
              Press ESC or SHIFT to close
            </span>
          </div>
          
          {/* Search Bar */}
          <input
            type="text"
            placeholder="Search shorthand or description..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            autoFocus
          />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {Object.entries(filteredCategories).length === 0 ? (
            <div className="text-center text-gray-500 mt-8">
              No mappings found matching "{searchTerm}"
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(filteredCategories).map(([category, items]) => (
                <div key={category}>
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">
                    {category}
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {items.map(([key, value], idx) => (
                      <div
                        key={`${category}-${idx}`}
                        className="flex border border-gray-200 rounded-lg overflow-hidden hover:bg-gray-50 transition-colors"
                      >
                        <div className="px-3 py-2 bg-gray-100 font-mono text-sm font-semibold text-gray-700 w-32 flex-shrink-0">
                          {key}
                        </div>
                        <div className="px-3 py-2 text-sm text-gray-600 flex-1">
                          {value}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-between text-xs text-gray-500">
            <span>Total: {Object.keys(mappings).length} mappings</span>
            <span>Showing: {Object.values(filteredCategories).flat().length} results</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MappingReference;