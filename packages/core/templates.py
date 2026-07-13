# packages/core/templates.py

# This is our "Vault" of pre-audited, human-written React/Tailwind components.
# The AI Brain will NEVER write raw React code from scratch. 
# It will only select components from this vault.
# This guarantees zero hallucinated imports and perfect, syntactically correct code.

TEMPLATE_VAULT = {
    "NavBar": """
import React from 'react';

const NavBar = ({ title, accentColor }) => {
  return (
    <nav className="flex items-center justify-between p-4 border-b" style={{ borderColor: accentColor }}>
      <h1 className="text-2xl font-bold text-gray-800">{title}</h1>
      <button 
        className="px-4 py-2 text-white font-semibold rounded-lg shadow-md hover:opacity-90 transition"
        style={{ backgroundColor: accentColor }}
      >
        Primary Action
      </button>
    </nav>
  );
};

export default NavBar;
""",
    "DataGrid": """
import React from 'react';

const DataGrid = ({ columns, data }) => {
  return (
    <div className="p-6">
      <table className="min-w-full bg-white border border-gray-200 rounded-lg shadow-sm">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col, index) => (
              <th key={index} className="py-3 px-4 text-left text-sm font-medium text-gray-500 uppercase tracking-wider">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {data.map((row, rowIndex) => (
            <tr key={rowIndex} className="hover:bg-gray-50 transition-colors">
              {columns.map((col, colIndex) => (
                <td key={colIndex} className="py-3 px-4 text-sm text-gray-700">
                  {row[col] || '-'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataGrid;
"""
}