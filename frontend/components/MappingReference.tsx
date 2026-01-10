import React, { useState, useMemo } from 'react';

interface MappingReferenceProps {
  isOpen: boolean;
  mappings: Record<string, string>;
}

// Parse section from key format "key [SECTION]"
const parseKeyAndSection = (fullKey: string): { key: string; section: string | null } => {
  const match = fullKey.match(/^(.+?) \[(.+)\]$/);
  if (match) {
    return { key: match[1], section: match[2] };
  }
  return { key: fullKey, section: null };
};

// Get section badge color
const getSectionColor = (section: string | null): string => {
  switch (section) {
    case 'MAIN BODY':
      return 'bg-blue-100 text-blue-700';
    case 'CONCLUSION':
      return 'bg-green-100 text-green-700';
    case 'COMMENTS':
      return 'bg-purple-100 text-purple-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
};

const MappingReference: React.FC<MappingReferenceProps> = ({ isOpen, mappings }) => {
  const [searchTerm, setSearchTerm] = useState('');

  // Categorize mappings (keys now include section labels like "key [SECTION]")
  const categorizedMappings = useMemo(() => {
    const categories: Record<string, Array<[string, string, string | null]>> = {
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

    Object.entries(mappings).forEach(([fullKey, value]) => {
      const { key, section } = parseKeyAndSection(fullKey);
      const keyLower = key.toLowerCase();

      // Categorize based on key patterns
      if (keyLower.startsWith('!')) {
        categories['Headers'].push([key, value, section]);
      } else if (keyLower.match(/^(c|m|ct|cm|cct|mct|cmct)$/) || keyLower.match(/^\d+c\d+m/)) {
        categories['Sample Description'].push([key, value, section]);
      } else if (keyLower.match(/(^tg|^gs|^ss|^mm\d|^mc\d|^isch|^g\d|^cg\d|^fn|^cc|^mexp|^mamyl|^gnorm|^ght|^eseg|^edif|^ccr|^fccr|^fcr)/)) {
        categories['Glomeruli'].push([key, value, section]);
      } else if (keyLower.match(/(^ati|^ifta|^t\d|^i\d|^ti\d|^ctci|^ct\d|^ci\d|^np)/)) {
        categories['Tubulointerstitium'].push([key, value, section]);
      } else if (keyLower.match(/(^a\d|^cv\d|^v\d|^ah\d|^ptc\d|^caa|il|ar$)/)) {
        categories['Blood Vessels'].push([key, value, section]);
      } else if (keyLower.match(/(^c4d|^sv40)/)) {
        categories['Immunohistochemistry'].push([key, value, section]);
      } else if (keyLower.match(/^em|^tb$|^lm$|^hb$/)) {
        categories['Electron Microscopy'].push([key, value, section]);
      } else if (keyLower.match(/(^fr|^iffr|^if)/)) {
        categories['Immunofluorescence'].push([key, value, section]);
      } else if (section === 'CONCLUSION') {
        categories['Conclusion'].push([key, value, section]);
      } else if (section === 'COMMENTS') {
        categories['Comment'].push([key, value, section]);
      } else {
        categories['Other'].push([key, value, section]);
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

    const filtered: Record<string, Array<[string, string, string | null]>> = {};
    const searchLower = searchTerm.toLowerCase();

    Object.entries(categorizedMappings).forEach(([category, items]) => {
      const filteredItems = items.filter(([key, value, section]) =>
        key.toLowerCase().includes(searchLower) ||
        value.toLowerCase().includes(searchLower) ||
        (section && section.toLowerCase().includes(searchLower))
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
                    {items.map(([key, value, section], idx) => (
                      <div
                        key={`${category}-${key}-${section}-${idx}`}
                        className="flex border border-gray-200 rounded-lg overflow-hidden hover:bg-gray-50 transition-colors"
                      >
                        <div className="px-3 py-2 bg-gray-100 font-mono text-sm font-semibold text-gray-700 w-40 flex-shrink-0 flex items-center gap-2">
                          <span>{key}</span>
                          {section && (
                            <span className={`px-1.5 py-0.5 text-xs rounded ${getSectionColor(section)}`}>
                              {section === 'MAIN BODY' ? 'MB' : section === 'CONCLUSION' ? 'CON' : 'COM'}
                            </span>
                          )}
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