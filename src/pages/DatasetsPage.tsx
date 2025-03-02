// src/pages/DatasetsPage.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, Filter, ArrowDownUp } from 'lucide-react';

function DatasetsPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('date');

  // Simular una lista de datasets (en producción, cargarías estos datos de una API)
  const datasets = [
    { id: 1, name: "Sales Performance Q1", category: "Marketing", records: 2854, lastUpdated: "2025-02-10" },
    { id: 2, name: "User Engagement Analytics", category: "Product", records: 4521, lastUpdated: "2025-02-15" },
    { id: 3, name: "Financial Projections 2025", category: "Finance", records: 1203, lastUpdated: "2025-01-28" },
    { id: 4, name: "Customer Behavior Data", category: "Research", records: 9652, lastUpdated: "2025-02-18" },
    { id: 5, name: "Supply Chain Metrics", category: "Operations", records: 3254, lastUpdated: "2025-02-05" },
    { id: 6, name: "Employee Performance Review", category: "HR", records: 489, lastUpdated: "2025-02-12" },
    { id: 7, name: "Social Media Campaign Results", category: "Marketing", records: 1835, lastUpdated: "2025-02-20" },
    { id: 8, name: "Product Feedback Analysis", category: "Product", records: 2741, lastUpdated: "2025-01-30" },
  ];

  // Filtrar y ordenar datasets
  const filteredDatasets = datasets
    .filter(dataset => 
      dataset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      dataset.category.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      if (sortBy === 'category') return a.category.localeCompare(b.category);
      if (sortBy === 'size') return b.records - a.records;
      return new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime(); // Por defecto, ordenar por fecha
    });

  const handleDatasetClick = (id: number) => {
    navigate(`/datasets/${id}`);
  };

  const getCategoryColor = (category: string) => {
    const categoryColors: Record<string, string> = {
      "Marketing": "bg-teal-800 text-teal-300",
      "Product": "bg-blue-800 text-blue-300",
      "Finance": "bg-purple-800 text-purple-300",
      "Research": "bg-pink-800 text-pink-300",
      "Operations": "bg-amber-800 text-amber-300",
      "HR": "bg-indigo-800 text-indigo-300"
    };
    
    return categoryColors[category] || "bg-gray-800 text-gray-300";
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
        <h1 className="text-2xl font-bold text-white">Datasets</h1>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <input
              type="text"
              placeholder="Search datasets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 bg-cyber-detail/50 border border-cyber-detail text-white rounded-lg focus:outline-none focus:ring-1 focus:ring-cyber-cyan"
            />
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          </div>
          
          <div className="relative group">
            <button className="p-2 bg-cyber-detail/50 border border-cyber-detail text-white rounded-lg hover:bg-cyber-detail/70">
              <Filter size={18} />
            </button>
            <div className="hidden group-hover:block absolute right-0 mt-2 w-48 bg-cyber-dark border border-cyber-detail rounded-lg shadow-lg z-10">
              <div className="p-2">
                <p className="text-xs text-gray-400 mb-2">Sort by</p>
                {['date', 'name', 'category', 'size'].map(option => (
                  <button
                    key={option}
                    className={`block w-full text-left px-4 py-2 text-sm rounded ${
                      sortBy === option ? 'bg-cyber-detail text-cyber-cyan' : 'text-white hover:bg-cyber-detail/50'
                    }`}
                    onClick={() => setSortBy(option)}
                  >
                    {option.charAt(0).toUpperCase() + option.slice(1)}
                    {sortBy === option && <span className="ml-2">✓</span>}
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          <button 
            className="flex items-center gap-2 px-4 py-2 bg-cyber-cyan text-cyber-dark rounded-lg hover:bg-cyan-300"
            onClick={() => alert("Add dataset functionality would go here")}
          >
            <Plus size={18} />
            <span>New Dataset</span>
          </button>
        </div>
      </div>

      {/* Lista de datasets */}
      <div className="bg-black/50 backdrop-blur-sm rounded-lg border border-gray-600 overflow-hidden">
        <div className="grid grid-cols-12 bg-cyber-detail/80 px-4 py-3 text-sm font-medium text-gray-300">
          <div className="col-span-5">Name</div>
          <div className="col-span-2">Category</div>
          <div className="col-span-2 flex items-center">
            Records
            <ArrowDownUp size={14} className="ml-1" />
          </div>
          <div className="col-span-3 flex items-center">
            Last Updated
            <ArrowDownUp size={14} className="ml-1" />
          </div>
        </div>
        
        <div className="divide-y divide-gray-700">
          {filteredDatasets.length > 0 ? (
            filteredDatasets.map(dataset => (
              <div 
                key={dataset.id}
                className="grid grid-cols-12 px-4 py-4 hover:bg-cyber-detail/20 cursor-pointer transition-colors"
                onClick={() => handleDatasetClick(dataset.id)}
              >
                <div className="col-span-5">
                  <p className="font-medium text-white">{dataset.name}</p>
                </div>
                <div className="col-span-2">
                  <span className={`px-2 py-1 rounded text-xs ${getCategoryColor(dataset.category)}`}>
                    {dataset.category}
                  </span>
                </div>
                <div className="col-span-2 text-gray-300">
                  {dataset.records.toLocaleString()}
                </div>
                <div className="col-span-3 text-gray-300">
                  {new Date(dataset.lastUpdated).toLocaleDateString()}
                </div>
              </div>
            ))
          ) : (
            <div className="px-4 py-8 text-center text-gray-400">
              No datasets found matching your search criteria
            </div>
          )}
        </div>
      </div>

      {/* Paginación */}
      <div className="flex justify-between items-center">
        <p className="text-sm text-gray-400">Showing {filteredDatasets.length} of {datasets.length} datasets</p>
        
        <div className="flex space-x-1">
          <button className="px-3 py-1 bg-cyber-detail/50 border border-cyber-detail text-white rounded hover:bg-cyber-detail/70">
            Previous
          </button>
          <button className="px-3 py-1 bg-cyber-cyan text-cyber-dark rounded">
            1
          </button>
          <button className="px-3 py-1 bg-cyber-detail/50 border border-cyber-detail text-white rounded hover:bg-cyber-detail/70">
            2
          </button>
          <button className="px-3 py-1 bg-cyber-detail/50 border border-cyber-detail text-white rounded hover:bg-cyber-detail/70">
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

export default DatasetsPage;