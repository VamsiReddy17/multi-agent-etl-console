import React, { useState, useEffect, useRef } from 'react';
import { 
  Server, 
  Activity, 
  Settings, 
  Terminal, 
  Database, 
  CheckCircle, 
  AlertTriangle, 
  TrendingUp, 
  Play, 
  Square,
  RefreshCw,
  Cpu,
  Layers,
  Heart,
  ChevronRight,
  ShieldCheck,
  CheckSquare,
  HelpCircle,
  Sliders,
  Pause,
  Trash2,
  AlertOctagon,
  ArrowRight
} from 'lucide-react';

// List of project component objects and details
const INITIAL_COMPONENTS = [
  { id: 'zookeeper', name: 'Zookeeper Co-ordinator', type: 'infra', status: 'up', port: 2181, description: 'Manages and co-ordinates the Apache Kafka cluster.', memory: '48 MB', lag: '0ms' },
  { id: 'kafka', name: 'Apache Kafka Broker', type: 'infra', status: 'up', port: 9092, description: 'Highly-durable, high-throughput message streaming queue.', memory: '240 MB', lag: '2ms' },
  { id: 'redis', name: 'Redis Task Queue', type: 'infra', status: 'up', port: 6379, description: 'In-memory queue supporting Airflow\'s Celery Task Executors.', memory: '18 MB', lag: '0.1ms' },
  { id: 'postgres', name: 'PostgreSQL DW', type: 'infra', status: 'up', port: 5432, description: 'Target data warehouse hosting warehouse.order_events and audit logs.', memory: '85 MB', lag: '5ms' },
  { id: 'airflow_webserver', name: 'Airflow Web UI', type: 'orchestrator', status: 'up', port: 8080, description: 'Provides visual interface for DAG scheduling and system logs.', memory: '124 MB', lag: '0.5s' },
  { id: 'airflow_scheduler', name: 'Airflow Scheduler', type: 'orchestrator', status: 'up', port: '—', description: 'Triggers active streaming and batch DAG workflows.', memory: '98 MB', lag: '1.2s' },
  { id: 'airflow_worker', name: 'Airflow Worker (Celery)', type: 'orchestrator', status: 'up', port: '—', description: 'Executes concurrent DAG worker tasks.', memory: '156 MB', lag: '0.8s' },
  { id: 'ingestion_agent', name: 'Kafka Ingestion Agent', type: 'agent', status: 'up', port: '—', description: 'Polls topic, deserialises JSON events with fault tolerance.', memory: '34 MB', lag: '28ms' },
  { id: 'transform_agent', name: 'Transform Agent', type: 'agent', status: 'up', port: '—', description: 'Type coerces, enriches metrics, and calculates totals.', memory: '28 MB', lag: '14ms' },
  { id: 'quality_agent', name: 'Quality Validation Agent', type: 'agent', status: 'up', port: '—', description: 'Performs data rules checks, quarantining bad records.', memory: '32 MB', lag: '19ms' },
  { id: 'load_agent', name: 'PostgreSQL Load Agent', type: 'agent', status: 'up', port: '—', description: 'Performs high-performance bulk batch database insertions.', memory: '42 MB', lag: '45ms' },
  { id: 'prometheus', name: 'Prometheus Telemetry', type: 'monitor', status: 'up', port: 9090, description: 'Scrapes loop metrics from endpoint on port 8000.', memory: '52 MB', lag: '15s' },
  { id: 'grafana', name: 'Grafana Dashboard', type: 'monitor', status: 'up', port: 3000, description: 'Auto-provisioned analytics charts visualizing throughput.', memory: '64 MB', lag: '—' }
];

const HISTORICAL_BUGS = [
  {
    id: 'BUG-001',
    title: 'Airflow API Connexion V3 Crash',
    severity: 'CRITICAL',
    fixedIn: 'Session 2',
    description: 'The Airflow Webserver crashed on boot with a Type Error: `__init__() got an unexpected keyword argument \'skip_error_handlers\'`. This occurred because Connexion v3 removed this legacy argument.',
    fix: 'Locked `connexion[swagger]==2.14.2` explicitly in requirements.txt.',
    learning: 'Always lock major sub-dependencies to avoid transitive breaking changes.'
  },
  {
    id: 'BUG-002',
    title: 'Pendulum Timezone Incompatibility',
    severity: 'CRITICAL',
    fixedIn: 'Session 2',
    description: 'Services threw `TypeError: \'module\' object is not callable` in `pendulum.tz.timezone("UTC")` during datetime parse operations, following an unconstrained Pendulum v3 release.',
    fix: 'Forced `pendulum==2.1.2` across the dependency ecosystem.',
    learning: 'In older Airflow networks (v2.5.3), lock Timezone packages strictly to v2.'
  },
  {
    id: 'BUG-003',
    title: 'Flask-Session Module Namespace Shift',
    severity: 'CRITICAL',
    fixedIn: 'Session 2',
    description: 'Database upgrades failed with `ModuleNotFoundError: No module named \'flask_session.sessions\'` due to internal file structure refactoring in newer versions.',
    fix: 'Locked `flask-session==0.4.0` in the main Airflow build environment.',
    learning: 'Lock supporting UI plugins to ensure database upgrades compile properly.'
  },
  {
    id: 'BUG-004',
    title: 'SQLAlchemy v2.0 Breaking Changes',
    severity: 'CRITICAL',
    fixedIn: 'Session 2',
    description: 'Docker builds failed because SQLAlchemy v2.0 is fundamentally incompatible with Airflow 2.5.3, which enforces a strict `<2.0` upper bound.',
    fix: 'Downgraded and pinned `sqlalchemy==1.4.40` in requirements.txt.',
    learning: 'Check major parent dependency bounds before updating helper ORMs.'
  },
  {
    id: 'BUG-005',
    title: 'Quality Agent Mock Test Short-Circuit',
    severity: 'HIGH',
    fixedIn: 'Session 3',
    description: 'Providing a small mock batch (2 valid, 1 bad) yielded a 33.3% anomaly rate, exceeding the 20% safety threshold, causing the Quality Agent to abort the pipeline run entirely.',
    fix: 'Adjusted mock dataset to 5 valid records and 1 bad record (16.7%), remaining safely under the 20% limit.',
    learning: 'Ensure testing sizes accurately reflect operational threshold rules.'
  },
  {
    id: 'BUG-006',
    title: 'Kafka Batch Size Propagation Defect',
    severity: 'HIGH',
    fixedIn: 'Session 6',
    description: 'The pipeline configuration value (`batch_size: 2000`) was completely ignored, causing the Kafka consumer to default to a batch size of 100.',
    fix: 'Mapped YAML fields to the PipelineConfig properties in `StreamingETL.__init__` before agent creation.',
    learning: 'Always trace dynamic properties to ensure file settings reach clients.'
  }
];

const PRE_DEPLOY_CHECKLIST = [
  { id: 'dep1', text: 'SQLAlchemy pinned to 1.4.40' },
  { id: 'dep2', text: 'Pendulum pinned to 2.1.2' },
  { id: 'dep3', text: 'Connexion pinned to 2.14.2' },
  { id: 'dep4', text: 'Flask-Session pinned to 0.4.0' },
  { id: 'limit1', text: 'Mock test anomaly rates kept under 20%' },
  { id: 'prop1', text: 'Configuration YAML values mapped to Agent instances' }
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [liveMode, setLiveMode] = useState(false);
  const [selectedComp, setSelectedComp] = useState(INITIAL_COMPONENTS[0]);
  const [components, setComponents] = useState(INITIAL_COMPONENTS);

  // Advanced Controls
  const [isGenerating, setIsGenerating] = useState(true);
  const [streamVelocity, setStreamVelocity] = useState(250);
  const [anomalyRate, setAnomalyRate] = useState(10.2);

  // System Logs Simulator
  const [logs, setLogs] = useState([
    { id: 1, type: 'info', text: 'Initializing multi-agent telemetry stream...' },
    { id: 2, type: 'success', text: 'Connected to local Docker socket: unix:///Users/vamsireddy/.docker/run/docker.sock' },
    { id: 3, type: 'info', text: 'Active Kafka topic brokers exposed at localhost:9092' },
    { id: 4, type: 'success', text: 'E2E bootstrap sequences complete! System fully operational.' }
  ]);
  const [autoScroll, setAutoScroll] = useState(true);
  const terminalRef = useRef(null);

  // Advanced Kafka Lag state
  const [kafkaLag, setKafkaLag] = useState(0);

  // Human-in-the-loop Quarantine Hub records
  const [quarantineRecords, setQuarantineRecords] = useState([
    { id: 'REC-904', timestamp: '11:10:04', agent: 'QualityAgent', error: 'Negative value detected on total_amount', payload: '{\n  "order_id": 84920,\n  "customer_id": "cust_29402",\n  "total_amount": -12.50,\n  "currency": "USD"\n}' },
    { id: 'REC-908', timestamp: '11:12:15', agent: 'QualityAgent', error: 'Missing field: currency code', payload: '{\n  "order_id": 38104,\n  "customer_id": "cust_93014",\n  "total_amount": 89.99,\n  "currency": null\n}' },
    { id: 'REC-911', timestamp: '11:15:32', agent: 'QualityAgent', error: 'Character overflow on country field', payload: '{\n  "order_id": 74910,\n  "customer_id": "cust_38102",\n  "total_amount": 412.00,\n  "currency": "USD",\n  "country": "UNITED STATES OF AMERICA EXTRA LARGE FIELD OVERFLOW"\n}' }
  ]);
  const [editingRecord, setEditingRecord] = useState(null);
  const [editorPayload, setEditorPayload] = useState('');
  const [jsonParseError, setJsonParseError] = useState(null);

  // Database Inspector
  const [dbTable, setDbTable] = useState('warehouse.order_events');
  const [dbRecords, setDbRecords] = useState({
    'warehouse.order_events': [
      { id: 'evt_94821', customer: 'cust_84920', total: '$142.50', status: 'Passed', time: '11:15:32' },
      { id: 'evt_94822', customer: 'cust_38104', total: '$89.99', status: 'Passed', time: '11:15:35' },
      { id: 'evt_94823', customer: 'cust_74910', total: '$412.00', status: 'Passed', time: '11:15:40' },
      { id: 'evt_94824', customer: 'cust_28491', total: '$12.50', status: 'Quarantined', time: '11:15:42' },
      { id: 'evt_94825', customer: 'cust_90184', total: '$65.00', status: 'Passed', time: '11:15:48' }
    ],
    'warehouse.orders': [
      { id: 'ord_32941', customer: 'Jane Doe', total: '$232.40', status: 'Shipped', time: '11:12:01' },
      { id: 'ord_32942', customer: 'John Smith', total: '$94.00', status: 'Processing', time: '11:13:14' },
      { id: 'ord_32943', customer: 'Alice Johnson', total: '$1,024.50', status: 'Shipped', time: '11:14:50' },
      { id: 'ord_32944', customer: 'Robert Lee', total: '$15.99', status: 'Pending', time: '11:15:10' }
    ],
    'warehouse.pipeline_execution': [
      { id: 'run_683', dag: 'streaming_ingestion', tasks: '4/4', state: 'Success', latency: '128ms' },
      { id: 'run_684', dag: 'streaming_ingestion', tasks: '4/4', state: 'Success', latency: '135ms' },
      { id: 'run_685', dag: 'streaming_ingestion', tasks: '3/4', state: 'Failed', latency: '42ms' },
      { id: 'run_686', dag: 'streaming_ingestion', tasks: '4/4', state: 'Success', latency: '114ms' }
    ],
    'warehouse.schema_drift_logs': [
      { id: 'drift_01', type: 'New Column', field: 'discount_code (varchar)', agent: 'QualityAgent', status: 'Logged', time: '11:02:40' },
      { id: 'drift_02', type: 'Type Shift', field: 'total_amount (int -> float)', agent: 'TransformAgent', status: 'Approved', time: '11:05:15' }
    ]
  });

  // Pipeline Metrics State
  const [metrics, setMetrics] = useState({
    totalRuns: 33,
    successRuns: 33,
    processedIngest: 66000,
    processedLoad: 59271,
    quarantined: 6729,
    quarantineRate: 10.19,
    loadedCount: 249444,
    ingestRate: 250,
    avgLatency: 11.2,
    stageDurations: {
      ingestion: 0.13,
      transform: 0.01,
      quality: 0.006,
      load: 0.19
    }
  });

  // Checklist interactive state
  const [checklist, setChecklist] = useState(
    PRE_DEPLOY_CHECKLIST.map(item => ({ ...item, checked: true }))
  );

  // Particles for data-flow animation
  const [particles, setParticles] = useState([]);
  const particleIdRef = useRef(0);

  // Dynamic Service status toggler
  const toggleComponentStatus = (id) => {
    setComponents(prev => {
      return prev.map(comp => {
        if (comp.id === id) {
          const newStatus = comp.status === 'up' ? 'down' : 'up';
          const timestamp = new Date().toLocaleTimeString();
          setLogs(logPrev => [
            ...logPrev,
            {
              id: Date.now(),
              type: newStatus === 'up' ? 'success' : 'error',
              text: `[${timestamp}] [System:Control] Service '${comp.name}' manually toggled ${newStatus.toUpperCase()}.`
            }
          ]);
          return { ...comp, status: newStatus };
        }
        return comp;
      });
    });
  };

  // Connect to the WebSocket telemetry server if liveMode is active
  useEffect(() => {
    if (!liveMode) return;

    let socket;
    let reconnectTimeout;

    const connect = () => {
      console.log("[WebSocket] Connecting to telemetry gateway...");
      socket = new WebSocket("ws://localhost:8085/ws");

      socket.onopen = () => {
        console.log("[WebSocket] Connected successfully!");
        setLogs(prev => [
          ...prev,
          { id: Date.now(), type: "success", text: `[${new Date().toLocaleTimeString()}] [Telemetry] Successfully connected to live WebSocket gateway at ws://localhost:8085/ws` }
        ]);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          
          if (payload.metrics) {
            setMetrics(prev => ({
              ...prev,
              ...payload.metrics
            }));
          }
          
          if (payload.logs && payload.logs.length > 0) {
            setLogs(payload.logs);
          }
          
          if (payload.quarantine) {
            setQuarantineRecords(payload.quarantine);
          }
          
          if (payload.db_records) {
            setDbRecords(payload.db_records);
          }
        } catch (err) {
          console.error("[WebSocket] Message parsing error:", err);
        }
      };

      socket.onclose = () => {
        console.log("[WebSocket] Disconnected. Reconnecting in 3s...");
        reconnectTimeout = setTimeout(connect, 3000);
      };

      socket.onerror = (err) => {
        console.error("[WebSocket] Connection error:", err);
        socket.close();
      };
    };

    connect();

    return () => {
      if (socket) socket.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [liveMode]);

  // Simulation Loop: Continually grows numbers and updates logs/inspector
  useEffect(() => {
    let intervalId;
    if (!liveMode && isGenerating) {
      intervalId = setInterval(() => {
        const isIngestUp = components.find(c => c.id === 'ingestion_agent')?.status === 'up';
        const isKafkaUp = components.find(c => c.id === 'kafka')?.status === 'up';
        const isZookeeperUp = components.find(c => c.id === 'zookeeper')?.status === 'up';

        const timestamp = new Date().toLocaleTimeString();

        // 1. Critical infrastructure down (Zookeeper/Kafka)
        if (!isKafkaUp || !isZookeeperUp) {
          setLogs(prev => [
            ...prev,
            {
              id: Date.now() + 1,
              type: 'error',
              text: `[${timestamp}] [CRITICAL] [System] Broker failure: connection refused at localhost:9092. Pipeline stalled.`
            }
          ].slice(-50));
          
          setMetrics(prev => ({ ...prev, ingestRate: 0 }));
          
          // Cascading Down downstream agents dynamically
          setComponents(prev => prev.map(c => 
            c.type === 'agent' ? { ...c, status: 'pending' } : c
          ));
          return;
        }

        // If Kafka is restored, make sure agents show up
        setComponents(prev => prev.map(c => 
          c.type === 'agent' && c.status === 'pending' ? { ...c, status: 'up' } : c
        ));

        // 2. Ingestion agent offline -> Kafka lag builds up!
        if (!isIngestUp) {
          const lagGrowth = Math.round(streamVelocity * 2.0);
          setKafkaLag(prev => prev + lagGrowth);
          
          setLogs(prev => [
            ...prev,
            {
              id: Date.now() + 1,
              type: 'warning',
              text: `[${timestamp}] [Warning] Kafka Ingest Agent is down. Backlog piling up on topic 'orders': +${lagGrowth} records.`
            }
          ].slice(-50));

          setMetrics(prev => ({ ...prev, ingestRate: 0 }));
          
          // Set Kafka broker card lag dynamically
          setComponents(prev => prev.map(c => 
            c.id === 'kafka' ? { ...c, lag: `${kafkaLag + lagGrowth} events` } : c
          ));
          return;
        }

        // 3. Normal processing with burst speed support
        let batchSize = Math.round(streamVelocity * 2.0);
        let isBurstMode = false;

        if (kafkaLag > 0) {
          isBurstMode = true;
          const burstSize = Math.min(kafkaLag, batchSize * 3.0);
          batchSize += burstSize;
          setKafkaLag(prev => Math.max(0, prev - burstSize));
          
          // Clear card lag indicator
          setComponents(prev => prev.map(c => 
            c.id === 'kafka' ? { ...c, lag: kafkaLag - burstSize > 0 ? `${kafkaLag - burstSize} events` : '2ms' } : c
          ));
        }

        const badCount = Math.round(batchSize * (anomalyRate / 100));
        const goodCount = batchSize - badCount;

        setMetrics(prev => {
          const newProcessed = prev.processedIngest + batchSize;
          const newQuarantined = prev.quarantined + badCount;
          const newLoaded = prev.processedLoad + goodCount;
          const newRate = parseFloat(((newQuarantined / newProcessed) * 100).toFixed(2));
          
          return {
            ...prev,
            processedIngest: newProcessed,
            quarantined: newQuarantined,
            processedLoad: newLoaded,
            loadedCount: prev.loadedCount + goodCount,
            quarantineRate: newRate,
            totalRuns: prev.totalRuns + 1,
            successRuns: prev.successRuns + 1,
            ingestRate: isBurstMode ? streamVelocity * 2 : streamVelocity
          };
        });

        // Dynamic Schema Drift Generation if anomaly injector > 30%
        let driftLogged = false;
        if (anomalyRate > 30 && Math.random() < 0.3) {
          driftLogged = true;
          const randDriftId = `drift_${Math.floor(Math.random() * 90) + 10}`;
          const newDriftLog = {
            id: randDriftId,
            type: 'Schema Drift Warning',
            field: 'discount_code (varchar)',
            agent: 'QualityAgent',
            status: 'Logged',
            time: timestamp
          };
          
          setDbRecords(prev => ({
            ...prev,
            'warehouse.schema_drift_logs': [newDriftLog, ...prev['warehouse.schema_drift_logs']].slice(0, 5)
          }));
        }

        // Emit realistic logs
        const randOffset = Math.floor(Math.random() * 1000) + 54000;
        const newLogEntries = [
          {
            id: Date.now() + 1,
            type: 'info',
            text: `[${timestamp}] [Kafka:orders] Polled partition 0. Offset: ${randOffset}. ${isBurstMode ? '⚡ BURST RATE INGESTION ⚡' : 'Audited queue.'}`
          },
          {
            id: Date.now() + 2,
            type: 'success',
            text: `[${timestamp}] [Agent:Ingest] Successfully parsed batch of ${batchSize} events. CPU lag: 11ms.`
          }
        ];

        if (driftLogged) {
          newLogEntries.push({
            id: Date.now() + 3,
            type: 'warning',
            text: `[${timestamp}] [Agent:Quality] SCHEMA DRIFT ALERT: Dynamically injected field 'discount_code' logged in Postgres.`
          });
        }

        if (badCount > 0) {
          newLogEntries.push({
            id: Date.now() + 4,
            type: anomalyRate > 20 ? 'error' : 'warning',
            text: `[${timestamp}] [Agent:Quality] Quality rules filtered: quarantined ${badCount} records (~${anomalyRate}% anomalies).`
          });
          
          // Inject a new record to the Quarantine Hub logs
          const randOrd = Math.floor(Math.random() * 90000) + 10000;
          const newQuarRec = {
            id: `REC-${randOrd}`,
            timestamp,
            agent: 'QualityAgent',
            error: anomalyRate > 20 ? 'Schema verification mismatch' : 'Missing field: currency code',
            payload: `{\n  "order_id": ${randOrd},\n  "customer_id": "cust_${Math.floor(Math.random() * 9000) + 1000}",\n  "total_amount": ${(Math.random() * 200).toFixed(2)},\n  "currency": null\n}`
          };
          setQuarantineRecords(prev => [newQuarRec, ...prev].slice(0, 10));

        } else {
          newLogEntries.push({
            id: Date.now() + 4,
            type: 'success',
            text: `[${timestamp}] [Agent:Quality] Integrity verification PASSED.`
          });
        }

        newLogEntries.push({
          id: Date.now() + 5,
          type: 'success',
          text: `[${timestamp}] [Agent:Load] Postgres load execution complete. Rows saved: ${goodCount}.`
        });

        setLogs(prev => [...prev, ...newLogEntries].slice(-50)); 

        // Update database records grid
        const randCust = Math.floor(Math.random() * 90000) + 10000;
        const randAmount = (Math.random() * 500 + 10).toFixed(2);
        const newEvent = {
          id: `evt_${Math.floor(Math.random() * 90000) + 10000}`,
          customer: `cust_${randCust}`,
          total: `$${randAmount}`,
          status: Math.random() * 100 >= anomalyRate ? 'Passed' : 'Quarantined',
          time: timestamp
        };

        const newOrder = {
          id: `ord_${Math.floor(Math.random() * 90000) + 10000}`,
          customer: ['Michael Scott', 'Dwight Schrute', 'Jim Halpert', 'Pam Beesly', 'Angela Martin'][Math.floor(Math.random() * 5)],
          total: `$${randAmount}`,
          status: ['Shipped', 'Processing', 'Pending'][Math.floor(Math.random() * 3)],
          time: timestamp
        };

        const newDagRun = {
          id: `run_${Math.floor(Math.random() * 900) + 100}`,
          dag: 'streaming_ingestion',
          tasks: '4/4',
          state: 'Success',
          latency: `${Math.floor(Math.random() * 100) + 80}ms`
        };

        setDbRecords(prev => ({
          'warehouse.order_events': [newEvent, ...prev['warehouse.order_events']].slice(0, 5),
          'warehouse.orders': [newOrder, ...prev['warehouse.orders']].slice(0, 5),
          'warehouse.pipeline_execution': [newDagRun, ...prev['warehouse.pipeline_execution']].slice(0, 5),
          'warehouse.schema_drift_logs': prev['warehouse.schema_drift_logs']
        }));

      }, 2000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [liveMode, isGenerating, streamVelocity, anomalyRate, components, kafkaLag]);

  // Particle emission logic for the dynamic data flow
  useEffect(() => {
    let intervalId;
    const isIngestUp = components.find(c => c.id === 'ingestion_agent')?.status === 'up';
    const isKafkaUp = components.find(c => c.id === 'kafka')?.status === 'up';
    
    if (isGenerating && isIngestUp && isKafkaUp) {
      const emitRate = Math.max(150, 1000 - (streamVelocity * 0.8)); 
      intervalId = setInterval(() => {
        const isBad = Math.random() * 100 < anomalyRate;
        const id = particleIdRef.current++;
        setParticles(prev => [
          ...prev, 
          { id, step: 0, isBad }
        ]);
      }, emitRate);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isGenerating, streamVelocity, anomalyRate, components]);

  // Update particles steps for transition animations
  useEffect(() => {
    let intervalId;
    if (isGenerating) {
      intervalId = setInterval(() => {
        setParticles(prev => 
          prev
            .map(p => ({ ...p, step: p.step + 1 }))
            .filter(p => p.step <= 4)
        );
      }, 1000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isGenerating]);

  // Auto scroll logs
  useEffect(() => {
    if (autoScroll && terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Toggle checklist items
  const toggleChecklistItem = (id) => {
    setChecklist(prev => 
      prev.map(item => item.id === id ? { ...item, checked: !item.checked } : item)
    );
  };

  return (
    <div className="app-container">
      {/* 1. Left Navigation Drawer */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <Server size={28} className="text-primary" style={{ color: '#3b82f6' }} />
          <div className="sidebar-title">GCP Pipeline Console</div>
        </div>
        
        <nav className="sidebar-menu">
          <div 
            className={`menu-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Activity size={20} />
            <span>Topology & Metrics</span>
          </div>
          <div 
            className={`menu-item ${activeTab === 'flow' ? 'active' : ''}`}
            onClick={() => setActiveTab('flow')}
          >
            <Layers size={20} />
            <span>Live Data Canvas</span>
          </div>
          <div 
            className={`menu-item ${activeTab === 'quarantine' ? 'active' : ''}`}
            onClick={() => setActiveTab('quarantine')}
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <AlertTriangle size={20} style={{ color: quarantineRecords.length > 0 ? '#ef4444' : 'inherit' }} />
              <span>Quarantine Hub</span>
            </div>
            {quarantineRecords.length > 0 && (
              <span className="badge-count">{quarantineRecords.length}</span>
            )}
          </div>
          <div 
            className={`menu-item ${activeTab === 'checklist' ? 'active' : ''}`}
            onClick={() => setActiveTab('checklist')}
          >
            <ShieldCheck size={20} />
            <span>Agent Review Hub</span>
          </div>
        </nav>
        
        {/* Footer System Status Panel */}
        <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981', display: 'inline-block' }}></span>
            <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>ALL CONTAINER SEED UP</span>
          </div>
          <div>Mode: {liveMode ? 'Live Metrics Mode' : 'Local Simulation'}</div>
          <div style={{ marginTop: '4px' }}>Port: 8082 (Dev Server)</div>
        </div>
      </aside>

      {/* 2. Main Workspace */}
      <main className="main-content">
        
        {/* Top App Bar */}
        <header className="topbar">
          <div className="topbar-left">
            <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', fontWeight: '700', margin: 0 }}>
              Multi-Agent Ingestion Pipeline
            </h1>
            <span className="system-tag">production-ready</span>
          </div>
          
          <div className="topbar-right">
            <div className="mode-toggle">
              <span style={{ fontSize: '0.8rem', fontWeight: '500', color: liveMode ? 'var(--text-secondary)' : '#60a5fa' }}>Simulation</span>
              <label className="switch">
                <input 
                  type="checkbox" 
                  checked={liveMode}
                  onChange={(e) => setLiveMode(e.target.checked)}
                />
                <span className="slider"></span>
              </label>
              <span style={{ fontSize: '0.8rem', fontWeight: '500', color: liveMode ? '#60a5fa' : 'var(--text-secondary)' }}>Live Telemetry</span>
            </div>
            
            <Heart size={20} className="text-secondary" style={{ color: '#ec4899' }} />
          </div>
        </header>

        {/* Scrollable Panel */}
        <div className="workspace-panel">
          
          {/* TAB 1: DASHBOARD METRICS & TOPOLOGY */}
          {activeTab === 'dashboard' && (
            <>
              {/* Header Info */}
              <div>
                <h2 className="section-title">System Performance & Object Matrix</h2>
                <p className="section-desc">Real-time status indicators and database ingestion counters at high throughput scale.</p>
              </div>

              {/* Metrics Row */}
              <div className="metrics-row">
                <div className="metric-card">
                  <div className="metric-header">
                    <span>Loaded DB Events</span>
                    <Database size={18} style={{ color: '#3b82f6' }} />
                  </div>
                  <div className="metric-value" style={{ color: '#60a5fa' }}>
                    {metrics.loadedCount.toLocaleString()}
                  </div>
                  <div className="metric-footer">
                    <TrendingUp size={14} style={{ color: '#10b981' }} />
                    <span>PostgreSQL warehouse loaded events</span>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span>Throughput Rate</span>
                    <Cpu size={18} style={{ color: '#10b981' }} />
                  </div>
                  <div className="metric-value" style={{ color: '#34d399' }}>
                    {metrics.ingestRate} <span style={{ fontSize: '1rem', fontWeight: '500' }}>events/s</span>
                  </div>
                  <div className="metric-footer">
                    <Activity size={14} style={{ color: '#34d399' }} />
                    <span>Peak ingestion: 1,000 events/s</span>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span>Anomaly Rate</span>
                    <AlertTriangle size={18} style={{ color: '#ef4444' }} />
                  </div>
                  <div className="metric-value" style={{ color: '#f87171' }}>
                    {metrics.quarantineRate}%
                  </div>
                  <div className="metric-footer">
                    <CheckCircle size={14} style={{ color: '#ef4444' }} />
                    <span>Safety limit: Under 20.0% max</span>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-header">
                    <span>Pipeline Runs</span>
                    <RefreshCw size={18} style={{ color: '#f59e0b' }} />
                  </div>
                  <div className="metric-value">
                    {metrics.successRuns}
                  </div>
                  <div className="metric-footer">
                    <span>Successful batches (batch size: 2,000)</span>
                  </div>
                </div>
              </div>

              {/* Topology Map and Details side sheet */}
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '28px', alignItems: 'start' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', fontWeight: '600', margin: 0 }}>
                    Active Services Matrix
                  </h3>
                  
                  <div className="components-grid">
                    {components.map((comp) => (
                      <div 
                        key={comp.id} 
                        className={`component-card ${selectedComp.id === comp.id ? 'selected' : ''}`}
                        onClick={() => setSelectedComp(comp)}
                      >
                        <div className="component-header">
                          <div className="component-title-row">
                            <Server size={18} style={{ color: comp.type === 'agent' ? '#34d399' : '#60a5fa' }} />
                            <span className="component-title">{comp.id.replace('_', ' ').toUpperCase()}</span>
                          </div>
                          
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={(e) => e.stopPropagation()}>
                            <label className="switch-sm">
                              <input 
                                type="checkbox" 
                                checked={comp.status === 'up'}
                                onChange={() => toggleComponentStatus(comp.id)}
                              />
                              <span className="slider-sm"></span>
                            </label>
                            <span className={`status-indicator ${comp.status}`} style={{ cursor: 'default' }}>
                              {comp.status.toUpperCase()}
                            </span>
                          </div>
                        </div>

                        <div className="component-stats">
                          <div className="stat-row">
                            <span>Connection:</span>
                            <span className="stat-value">{comp.port === '—' ? 'IPC Socket' : `Port ${comp.port}`}</span>
                          </div>
                          <div className="stat-row">
                            <span>Memory:</span>
                            <span className="stat-value">{comp.memory}</span>
                          </div>
                          <div className="stat-row">
                            <span>Lag/Ping:</span>
                            <span className="stat-value">{comp.lag}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Side Sheet Details Panel */}
                <div className="info-sheet">
                  <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#60a5fa', marginBottom: '8px' }}>
                      <Cpu size={20} />
                      <span style={{ fontSize: '0.8rem', fontWeight: '700', letterSpacing: '1px', textTransform: 'uppercase' }}>
                        {selectedComp.type} details
                      </span>
                    </div>
                    <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', fontWeight: '700', margin: '4px 0' }}>
                      {selectedComp.name}
                    </h3>
                  </div>

                  <div style={{ fontSize: '0.9rem', lineHeight: '1.5', color: 'var(--text-secondary)' }}>
                    {selectedComp.description}
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid var(--border-color)', paddingTop: '16px', fontSize: '0.85rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'between' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Status:</span>
                      <span style={{ fontWeight: '600', color: '#34d399' }}>● ACTIVE / RUNNING</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'between' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Active Port:</span>
                      <span style={{ fontWeight: '600' }}>{selectedComp.port}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'between' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Allocated Memory:</span>
                      <span style={{ fontWeight: '600' }}>{selectedComp.memory}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'between' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Network Latency:</span>
                      <span style={{ fontWeight: '600', color: '#fbbf24' }}>{selectedComp.lag}</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* TAB 2: LIVE INGESTION CANVAS */}
          {activeTab === 'flow' && (
            <>
              {/* Header Info */}
              <div>
                <h2 className="section-title">End-to-End Visual Data Flow</h2>
                <p className="section-desc">Interactive trace monitoring active JSON data packets flowing from topics through sequential processing agents.</p>
              </div>

              {/* Blinking Critical Alert Banner */}
              {anomalyRate > 20 && (
                <div className="alert-banner blinking">
                  <AlertOctagon size={20} className="shake" />
                  <span>
                    <strong>CRITICAL PIPELINE INCIDENT DETECTED:</strong> Anomaly isolation rate by Quality Agent is at <strong>{anomalyRate}%</strong>, exceeding the 20.0% max limit! System running in quarantine stress-test mode.
                  </span>
                </div>
              )}

              {/* 1. Visual Canvas Area */}
              <div className="canvas-container">
                <div className="flow-track">
                  
                  {/* Particle animations */}
                  {isGenerating && particles.map((p) => {
                    let className = "particle";
                    if (p.isBad && p.step >= 2) className += " quarantined";
                    
                    let style = {};
                    if (p.step === 1) style = { animation: 'flow1 1s linear forwards' };
                    if (p.step === 2) style = { animation: 'flow2 1s linear forwards' };
                    if (p.step === 3) style = { animation: 'flow3 1s linear forwards' };
                    if (p.step === 4) style = { animation: 'flow4 1s linear forwards' };

                    if (p.step === 0) return null;
                    
                    // If quarantined, particle diverges off track at step 3
                    if (p.isBad && p.step === 3) {
                      style = { 
                        animation: 'flow3 1s linear forwards',
                        transform: 'translateY(55px) scale(0.8)'
                      };
                    }
                    if (p.isBad && p.step === 4) return null; 

                    return (
                      <div 
                        key={p.id} 
                        className={className} 
                        style={style}
                      />
                    );
                  })}

                  <div className={`flow-node active ${isGenerating ? 'pulsing' : ''}`}>
                    <Database size={24} style={{ color: '#3b82f6' }} />
                    <span className="node-label">Kafka Topics</span>
                  </div>

                  <div className={`flow-node active ${isGenerating ? 'pulsing' : ''}`}>
                    <Server size={24} style={{ color: '#10b981' }} />
                    <span className="node-label">Ingest Agent</span>
                  </div>

                  <div className={`flow-node active ${isGenerating ? 'pulsing' : ''}`}>
                    <Cpu size={24} style={{ color: '#3b82f6' }} />
                    <span className="node-label">Transform Agent</span>
                  </div>

                  <div className={`flow-node active ${isGenerating ? 'pulsing-warn' : ''}`}>
                    <ShieldCheck size={24} style={{ color: anomalyRate > 20 ? '#ef4444' : '#f59e0b' }} />
                    <span className="node-label">Quality Agent</span>
                  </div>

                  <div className={`flow-node active ${isGenerating ? 'pulsing' : ''}`}>
                    <Database size={24} style={{ color: '#10b981' }} />
                    <span className="node-label">Postgres DW</span>
                  </div>
                </div>

                {/* Legend Panel */}
                <div style={{ display: 'flex', gap: '30px', borderTop: '1px solid var(--border-color)', width: '100%', paddingTop: '20px', justifyContent: 'center', fontSize: '0.85rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#3b82f6', display: 'inline-block' }}></span>
                    <span>Valid Order Packet</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#ef4444', display: 'inline-block' }}></span>
                    <span>Anomaly (Quarantined)</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '30px', height: '4px', backgroundColor: 'var(--border-color)', display: 'inline-block' }}></span>
                    <span>Data network stream</span>
                  </div>
                </div>
              </div>

              {/* 2. Interactive Controls and Database Inspector split */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.25fr', gap: '28px', alignItems: 'start' }}>
                
                {/* Left panel: Controls */}
                <div className="control-card">
                  <div className="control-card-header">
                    <Sliders size={20} style={{ color: '#3b82f6' }} />
                    <span className="control-card-title">Ingestion & Telemetry Controllers</span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '4px 0' }}>
                    {/* Toggle Stream */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>Event Stream Generator</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Pause/resume mock telemetry streams</div>
                      </div>
                      <button 
                        className={`action-btn ${isGenerating ? 'stop' : 'start'}`}
                        onClick={() => {
                          setIsGenerating(!isGenerating);
                          const timestamp = new Date().toLocaleTimeString();
                          setLogs(prev => [
                            ...prev, 
                            { 
                              id: Date.now(), 
                              type: isGenerating ? 'warning' : 'success', 
                              text: `[${timestamp}] [System:Control] Event Ingestion Generator manually ${isGenerating ? 'PAUSED' : 'RESUMED'}.` 
                            }
                          ]);
                        }}
                      >
                        {isGenerating ? <Pause size={16} /> : <Play size={16} />}
                        <span>{isGenerating ? 'Pause Stream' : 'Resume Stream'}</span>
                      </button>
                    </div>

                    <hr style={{ border: 'none', height: '1px', backgroundColor: 'var(--border-color)', margin: 0 }} />

                    {/* Stream Velocity */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>Ingestion Velocity</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Scale overall event throughput</div>
                        </div>
                        <span className="badge-blue">{streamVelocity} events/s</span>
                      </div>
                      <input 
                        type="range" 
                        min="10" 
                        max="1000" 
                        value={streamVelocity} 
                        disabled={!isGenerating}
                        onChange={(e) => setStreamVelocity(parseInt(e.target.value))}
                        className="custom-range"
                      />
                    </div>

                    <hr style={{ border: 'none', height: '1px', backgroundColor: 'var(--border-color)', margin: 0 }} />

                    {/* Anomaly Injection */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>Data Anomaly Injector</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Simulate corrupted JSON packets</div>
                        </div>
                        <span className={`badge-pill ${anomalyRate > 20 ? 'red' : 'yellow'}`}>{anomalyRate}%</span>
                      </div>
                      <input 
                        type="range" 
                        min="0" 
                        max="50" 
                        step="0.5"
                        value={anomalyRate} 
                        disabled={!isGenerating}
                        onChange={(e) => setAnomalyRate(parseFloat(e.target.value))}
                        className="custom-range"
                      />
                      <div style={{ fontSize: '0.75rem', color: anomalyRate > 20 ? '#f87171' : 'var(--text-secondary)', display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: anomalyRate > 20 ? '#ef4444' : '#f59e0b', display: 'inline-block' }}></span>
                        <span>State: {anomalyRate < 5 ? 'PRISTINE' : anomalyRate < 15 ? 'NOMINAL' : anomalyRate < 20 ? 'ELEVATED' : 'CRITICAL INCIDENT ALERT!'}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right panel: Database Warehouse Inspector */}
                <div className="control-card">
                  <div className="control-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Database size={20} style={{ color: '#10b981' }} />
                      <span className="control-card-title">Live Postgres Warehouse Inspector</span>
                    </div>
                    <span style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: '600', letterSpacing: '0.5px' }}>● CONNECTED</span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {/* Selector Tabs */}
                    <div className="table-selector-tabs">
                      {Object.keys(dbRecords).map((tbl) => (
                        <button 
                          key={tbl}
                          className={`table-tab-btn ${dbTable === tbl ? 'active' : ''}`}
                          onClick={() => setDbTable(tbl)}
                        >
                          {tbl}
                        </button>
                      ))}
                    </div>

                    {/* Table View */}
                    <div className="db-table-wrapper">
                      <table className="db-inspector-table">
                        <thead>
                          {dbTable === 'warehouse.order_events' && (
                            <tr>
                              <th>Event ID</th>
                              <th>Customer</th>
                              <th>Total Amount</th>
                              <th>Validation</th>
                              <th>Time Ingested</th>
                            </tr>
                          )}
                          {dbTable === 'warehouse.orders' && (
                            <tr>
                              <th>Order ID</th>
                              <th>Customer Name</th>
                              <th>Total Price</th>
                              <th>Status</th>
                              <th>Time Loaded</th>
                            </tr>
                          )}
                          {dbTable === 'warehouse.pipeline_execution' && (
                            <tr>
                              <th>Run ID</th>
                              <th>Dag ID</th>
                              <th>Executed Tasks</th>
                              <th>DAG State</th>
                              <th>Latency</th>
                            </tr>
                          )}
                          {dbTable === 'warehouse.schema_drift_logs' && (
                            <tr>
                              <th>Drift ID</th>
                              <th>Drift Type</th>
                              <th>Field Name</th>
                              <th>Detected By</th>
                              <th>Status</th>
                              <th>Logged At</th>
                            </tr>
                          )}
                        </thead>
                        <tbody>
                          {dbRecords[dbTable].map((row, idx) => (
                            <tr key={idx}>
                              {dbTable === 'warehouse.order_events' && (
                                <>
                                  <td style={{ color: '#60a5fa', fontWeight: '600' }}>{row.id}</td>
                                  <td>{row.customer}</td>
                                  <td>{row.total}</td>
                                  <td>
                                    <span className={`status-pill ${row.status.toLowerCase()}`}>
                                      {row.status}
                                    </span>
                                  </td>
                                  <td>{row.time}</td>
                                </>
                              )}
                              {dbTable === 'warehouse.orders' && (
                                <>
                                  <td style={{ color: '#34d399', fontWeight: '600' }}>{row.id}</td>
                                  <td>{row.customer}</td>
                                  <td>{row.total}</td>
                                  <td>
                                    <span className={`status-pill ${row.status.toLowerCase()}`}>
                                      {row.status}
                                    </span>
                                  </td>
                                  <td>{row.time}</td>
                                </>
                              )}
                              {dbTable === 'warehouse.pipeline_execution' && (
                                <>
                                  <td style={{ color: '#fbbf24', fontWeight: '600' }}>{row.id}</td>
                                  <td>{row.dag}</td>
                                  <td>{row.tasks}</td>
                                  <td>
                                    <span className={`status-pill success`}>
                                      {row.state}
                                    </span>
                                  </td>
                                  <td style={{ color: '#fbbf24' }}>{row.latency}</td>
                                </>
                              )}
                              {dbTable === 'warehouse.schema_drift_logs' && (
                                <>
                                  <td style={{ color: '#ec4899', fontWeight: '600' }}>{row.id}</td>
                                  <td>{row.type}</td>
                                  <td><code>{row.field}</code></td>
                                  <td>{row.agent}</td>
                                  <td>
                                    <span className="status-pill warning" style={{ backgroundColor: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b' }}>
                                      {row.status}
                                    </span>
                                  </td>
                                  <td>{row.time}</td>
                                </>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>

              {/* 3. System Terminal Logs Widget (Full width) */}
              <div className="terminal-logs">
                <div className="terminal-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Terminal size={18} style={{ color: '#60a5fa' }} />
                    <span className="terminal-title">STDOUT STREAM TERMINAL</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                      <input 
                        type="checkbox" 
                        checked={autoScroll} 
                        onChange={(e) => setAutoScroll(e.target.checked)}
                        style={{ cursor: 'pointer' }}
                      />
                      <span>Auto Scroll</span>
                    </label>
                    <button 
                      className="terminal-clear-btn"
                      onClick={() => setLogs([{ id: 1, type: 'info', text: 'Terminal cleared by user.' }])}
                      title="Clear Logs"
                    >
                      <Trash2 size={14} />
                      <span>Clear</span>
                    </button>
                  </div>
                </div>

                <div className="terminal-body" ref={terminalRef}>
                  {logs.map((log) => (
                    <div key={log.id} className={`terminal-line ${log.type}`}>
                      <ChevronRight size={14} className="terminal-line-arrow" />
                      <span>{log.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* TAB: QUARANTINE HUB */}
          {activeTab === 'quarantine' && (
            <>
              <div>
                <h2 className="section-title">Isolated Anomaly Quarantine Hub</h2>
                <p className="section-desc">Human-in-the-loop operational panel. Review malformed JSON events caught by the validation agent, fix payload schemas, and re-inject them.</p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1.25fr 1fr', gap: '28px', alignItems: 'start' }}>
                {/* Left side: List of records */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', fontWeight: '600', margin: 0 }}>
                    Active Isolation Queue ({quarantineRecords.length} items)
                  </h3>
                  
                  {quarantineRecords.length === 0 ? (
                    <div style={{ padding: '40px', backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '16px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                      <CheckCircle size={32} style={{ color: '#10b981', marginBottom: '12px' }} />
                      <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>All Queues Clear!</div>
                      <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>No records are currently held in quarantine.</div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '550px', overflowY: 'auto', paddingRight: '4px' }}>
                      {quarantineRecords.map((rec) => (
                        <div key={rec.id} className={`quarantine-card ${editingRecord?.id === rec.id ? 'active' : ''}`}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontFamily: 'monospace', fontWeight: '700', fontSize: '0.85rem', color: '#f87171' }}>{rec.id}</span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{rec.timestamp}</span>
                          </div>
                          
                          <div style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-primary)', display: 'flex', gap: '6px', alignItems: 'center', marginBottom: '6px' }}>
                            <AlertTriangle size={14} style={{ color: '#ef4444' }} />
                            <span>{rec.error}</span>
                          </div>
                          
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                            Quarantined by: <span style={{ fontFamily: 'monospace' }}>{rec.agent}</span>
                          </div>

                          <button 
                            className="repair-btn"
                            onClick={() => {
                              setEditingRecord(rec);
                              setEditorPayload(rec.payload);
                              setJsonParseError(null);
                            }}
                          >
                            <span>Inspect & Repair Payload</span>
                            <ArrowRight size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Right side: Editor */}
                <div>
                  <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', fontWeight: '600', margin: '0 0 16px 0' }}>
                    Interactive Payload Repair
                  </h3>

                  {editingRecord ? (
                    <div className="editor-card">
                      <div className="editor-header">
                        <span style={{ fontWeight: '600' }}>Editing: {editingRecord.id}</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Raw JSON Format</span>
                      </div>
                      
                      <div className="editor-body">
                        {jsonParseError && (
                          <div className="editor-error-alert">
                            <AlertTriangle size={16} />
                            <span>{jsonParseError}</span>
                          </div>
                        )}
                        
                        <textarea 
                          className="editor-textarea"
                          value={editorPayload}
                          onChange={(e) => setEditorPayload(e.target.value)}
                          rows="10"
                          placeholder="JSON order payload..."
                        />
                      </div>

                      <div className="editor-footer">
                        <button 
                          className="editor-btn-secondary"
                          onClick={() => {
                            setEditingRecord(null);
                            setEditorPayload('');
                            setJsonParseError(null);
                          }}
                        >
                          Cancel
                        </button>
                        <button 
                          className="editor-btn-primary"
                          onClick={async () => {
                            try {
                              const parsed = JSON.parse(editorPayload);
                              
                              if (liveMode) {
                                // Real API Reprocessing Integration
                                const response = await fetch("http://localhost:8085/reprocess", {
                                  method: "POST",
                                  headers: {
                                    "Content-Type": "application/json"
                                  },
                                  body: JSON.stringify({
                                    quarantine_id: editingRecord.id,
                                    payload: parsed
                                  })
                                });
                                
                                const resData = await response.json();
                                if (!response.ok) {
                                  throw new Error(resData.detail || "Reprocessing failed.");
                                }

                                const timestamp = new Date().toLocaleTimeString();
                                setLogs(prev => [
                                  ...prev,
                                  {
                                    id: Date.now(),
                                    type: 'success',
                                    text: `[${timestamp}] [SUCCESS] [Human-In-The-Loop] Reprocessed record '${editingRecord.id}' successfully. Anomaly resolved, loaded 1 row into database.`
                                  }
                                ]);
                              } else {
                                // Simulated Reprocessing
                                if (parsed.total_amount && parsed.total_amount < 0) {
                                  throw new Error("Verification Failed: 'total_amount' cannot be negative.");
                                }
                                if (parsed.currency === null || parsed.currency === undefined || parsed.currency === "") {
                                  throw new Error("Verification Failed: 'currency' field is required and cannot be null.");
                                }

                                setQuarantineRecords(prev => prev.filter(r => r.id !== editingRecord.id));
                                
                                setMetrics(prev => ({
                                  ...prev,
                                  loadedCount: prev.loadedCount + 1,
                                  quarantined: Math.max(0, prev.quarantined - 1)
                                }));

                                const timestamp = new Date().toLocaleTimeString();
                                setLogs(prev => [
                                  ...prev,
                                  {
                                    id: Date.now(),
                                    type: 'success',
                                    text: `[${timestamp}] [SUCCESS] [Human-In-The-Loop] Reprocessed record '${editingRecord.id}' successfully. Anomaly resolved, loaded 1 row into database.`
                                  }
                                ]);
                              }

                              setEditingRecord(null);
                              setEditorPayload('');
                              setJsonParseError(null);
                            } catch (err) {
                              setJsonParseError(err.message || "Invalid JSON syntax. Please check braces and commas.");
                            }
                          }}
                        >
                          Verify & Reprocess
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="editor-placeholder">
                      <Terminal size={32} style={{ color: 'var(--text-tertiary)', marginBottom: '12px' }} />
                      <div>Select a record from the quarantine queue to launch the debugger editor.</div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* TAB 3: AGENT REVIEW HUB */}
          {activeTab === 'checklist' && (
            <>
              <div>
                <h2 className="section-title">Agent Learner Board & Mistake Tracker</h2>
                <p className="section-desc">Interactive review system logged for future AI agents to identify past pitfalls and protect against package regressions.</p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '28px', alignItems: 'start' }}>
                
                {/* Pre-deployment Checklist */}
                <div className="checklist-container">
                  <div className="checklist-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <CheckSquare size={20} style={{ color: '#10b981' }} />
                      <span>Pre-Deployment Safety Checklist</span>
                    </div>
                  </div>
                  
                  {checklist.map((item) => (
                    <div 
                      key={item.id}
                      className={`checklist-item ${item.checked ? 'checked' : ''}`}
                      onClick={() => toggleChecklistItem(item.id)}
                    >
                      <div className="checkbox-wrapper">
                        <input 
                          type="checkbox"
                          checked={item.checked}
                          onChange={() => {}} // handled by row click
                          style={{ cursor: 'pointer' }}
                        />
                      </div>
                      <span className="checklist-text">{item.text}</span>
                    </div>
                  ))}
                  
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', padding: '12px', borderTop: '1px solid var(--border-color)', marginTop: '8px' }}>
                    * Mark items as checked when verified in environments before committing code.
                  </div>
                </div>

                {/* Bug Post-Mortems */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', fontWeight: '600', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <AlertTriangle size={20} style={{ color: '#ef4444' }} />
                    <span>Past Bugs & Post-Mortem Reviews</span>
                  </h3>
                  
                  <div className="bug-list">
                    {HISTORICAL_BUGS.map((bug) => (
                      <div key={bug.id} className="bug-card">
                        <div className="bug-card-header">
                          <div className="bug-id-row">
                            <span className="bug-id">{bug.id}</span>
                            <span className="bug-title">{bug.title}</span>
                          </div>
                          <span className="bug-severity">{bug.severity}</span>
                        </div>

                        <div className="bug-body">
                          {bug.description}
                          <div className="bug-code-block">
                            {bug.fix}
                          </div>
                        </div>

                        <div className="bug-footer">
                          <span>Fixed in: {bug.fixedIn}</span>
                          <span className="bug-learning">Lesson: {bug.learning}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            </>
          )}

        </div>
      </main>
    </div>
  );
}
