import { Database, File, Server, Search, Zap } from 'react-feather';

export const DATA_SOURCE_TYPES = [
  { 
    id: 'excel', 
    name: 'Excel', 
    icon: File
  },
  { 
    id: 'tabularfile', 
    name: 'Tabular Files', 
    icon: File
  },
  { 
    id: 'mysql', 
    name: 'MySQL', 
    icon: Database
  },
  { 
    id: 'sqlserver', 
    name: 'SQL Server', 
    icon: Database
  },
  { 
    id: 'postgresql', 
    name: 'PostgreSQL', 
    icon: Database
  },
  { 
    id: 'mongodb', 
    name: 'MongoDB', 
    icon: Server
  },
  { 
    id: 'elasticsearch', 
    name: 'Elasticsearch', 
    icon: Search
  },
  { 
    id: 'redis', 
    name: 'Redis', 
    icon: Zap
  }
]; 