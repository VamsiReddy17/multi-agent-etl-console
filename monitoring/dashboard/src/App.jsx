import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Server, Activity, Terminal, Database, CheckCircle, AlertTriangle, 
  TrendingUp, RefreshCw, Cpu, Layers, Heart, ShieldCheck, ChevronDown,
  ChevronRight, BookOpen, Zap, Eye, Clock, Bug, Wrench, Award,
  Play, Pause, Trash2, Check, Edit3, ArrowRight, Search, Command, Info
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════════
//  DATA: Sessions (The Chronicle)
// ═══════════════════════════════════════════════════════════════════════════════
const SESSIONS = [
  {
    id: 1, date: '2026-05-20', 
    title: 'Genesis — The Architecture Takes Shape',
    goal: 'Review workspace, build full production pipeline from scratch',
    summary: 'From an empty scaffold, 26 files were forged — 4 specialized agents, a streaming orchestrator, 2 Airflow DAGs, 5 test suites, and a complete architecture documentation library. The multi-agent cooperative pattern was established.',
    activities: [
      'Reviewed reference multi-agent pipeline architecture',
      'Built 4 specialized agents: Kafka Ingestion, Transform, Quality, Postgres Load',
      'Created streaming ETL orchestrator with single-run and loop modes',
      'Designed 2 Airflow DAGs for streaming and batch processing',
      'Wrote 5 test files covering unit and integration tests',
      'Generated architecture diagrams and comprehensive documentation'
    ],
    issues: [],
    fixes: [],
    tags: ['feature', 'feature', 'feature'],
    filesCreated: 26, testsPassing: 0, rowsLoaded: 0
  },
  {
    id: 2, date: '2026-05-20',
    title: 'Trial by Fire — The Dependency Wars',
    goal: 'Start Docker services, run pytest, resolve library version conflicts',
    summary: 'Six critical dependency conflicts were discovered and conquered. Connexion v3, Pendulum v3, Flask-Session, and SQLAlchemy all waged war against Airflow 2.5.3. Every battle was won through version pinning and methodical debugging.',
    activities: [
      'Started Docker Compose stack with 7 base containers',
      'Diagnosed 6 critical dependency conflicts in Airflow ecosystem',
      'Locked all sub-dependencies to compatible versions',
      'Created Airflow admin user and verified login',
      'Achieved 31 passing tests in 0.12s'
    ],
    issues: [
      'Connexion v3 removed skip_error_handlers parameter',
      'Pendulum v3 broke timezone module callable',
      'Flask-Session v0.8 refactored internal modules',
      'SQLAlchemy v2.0 fundamentally incompatible with Airflow 2.5.3',
      'Missing celery/redis in root requirements.txt',
      'Kafka provider package version not found on PyPI'
    ],
    fixes: [
      'Locked connexion[swagger]==2.14.2',
      'Forced pendulum==2.1.2',
      'Pinned flask-session==0.4.0',
      'Downgraded sqlalchemy==1.4.40',
      'Added celery, redis, and provider packages',
      'Updated kafka provider to 1.0.0'
    ],
    tags: ['bug', 'fix', 'fix', 'fix'],
    filesCreated: 0, testsPassing: 31, rowsLoaded: 0
  },
  {
    id: 3, date: '2026-05-21',
    title: 'The All-Seeing Eye — Observability Awakens',
    goal: 'Implement Prometheus & Grafana observability and instrument ETL metrics',
    summary: 'The pipeline gained sight. Prometheus began scraping 5 custom metrics, Grafana dashboards auto-provisioned with throughput visualizations, and the Quality Agent\'s quarantine threshold bug was tamed with smarter test parameters.',
    activities: [
      'Added Prometheus and Grafana containers to docker-compose',
      'Created auto-provisioning datasource and dashboard configs',
      'Built pipeline_dashboard.json with throughput and latency panels',
      'Instrumented streaming_etl.py with 5 Prometheus metrics',
      'Wrote test_metrics.py asserting correct telemetry values'
    ],
    issues: ['Quality test quarantine rate exceeded 20% threshold with small mock batches'],
    fixes: ['Adjusted test batch: 5 valid + 1 quarantined = 16.7% rate (under 20% limit)'],
    tags: ['feature', 'fix'],
    filesCreated: 4, testsPassing: 33, rowsLoaded: 0
  },
  {
    id: 4, date: '2026-05-21',
    title: 'The Infinite Loop — Metrics Go Live',
    goal: 'Verify metrics scraping, fix loop termination, and finalize integration',
    summary: 'The streaming pipeline achieved perpetual motion. The max_empty_polls bug that killed the daemon after 10 loops was discovered and eliminated. Prometheus confirmed target UP, Grafana rendered live dashboards, and the metrics endpoint blazed on port 8000.',
    activities: [
      'Verified all 9 containers running and healthy',
      'Fixed pipeline loop termination after 10 empty polls',
      'Started streaming loop daemon in background',
      'Confirmed Prometheus target UP and Grafana dashboard loaded',
      'Verified metrics endpoint active at localhost:8000'
    ],
    issues: ['Pipeline daemon terminated after 10 consecutive empty polls'],
    fixes: ['Set max_empty_polls to 0 (infinite) in pipeline_config.yaml'],
    tags: ['fix', 'perf'],
    filesCreated: 0, testsPassing: 33, rowsLoaded: 0
  },
  {
    id: 5, date: '2026-05-21',
    title: 'The Great Flood — Data Pours In',
    goal: 'Build continuous Kafka generator and verify full end-to-end pipeline',
    summary: 'The floodgates opened. A continuous order generator began producing 250 events/second. The AttributeError in generate_orders.py was slain, and the pipeline proved itself — ingesting, transforming, validating, and loading data at scale. 81+ rows accumulated and Prometheus counters climbed steadily.',
    activities: [
      'Diagnosed order generator crash on container startup',
      'Fixed AttributeError: args.bad-rate → args.bad_rate',
      'Restarted generator at 250 msg/s with 10% anomaly rate',
      'Launched continuous streaming ETL loop daemon',
      'Verified rows growing from 33 to 81+ in PostgreSQL',
      'Scaled batch size to 2000 and interval to 2s'
    ],
    issues: ['Generator crashed with AttributeError on args.bad-rate'],
    fixes: ['Fixed argparse attribute reference from args.bad-rate to args.bad_rate'],
    tags: ['bug', 'fix', 'perf'],
    filesCreated: 0, testsPassing: 33, rowsLoaded: 7280
  },
  {
    id: 6, date: '2026-05-21',
    title: 'The Crucible — 100,000 Rows Breached',
    goal: 'Fix config propagation bug and achieve 100,000+ rows ingested',
    summary: 'The hidden defect was found — batch_size: 2000 from YAML was never reaching the agents, causing them to crawl at batch 100. Dynamic config propagation was implemented, and the pipeline erupted: 109,000+ events loaded in minutes, peaking at 1,000 msg/s with a 10.19% quarantine rate.',
    activities: [
      'Identified batch_size propagation bug from YAML to agents',
      'Implemented dynamic YAML → PipelineConfig property mapping',
      'Restarted daemon with propagated 2000-message batches',
      'Achieved 109,000+ rows loaded in PostgreSQL',
      'Measured peak throughput of 1,000 messages/second',
      'Verified 10.19% quarantine rate (6,729 quarantined)'
    ],
    issues: ['YAML batch_size: 2000 silently ignored, defaulting to 100'],
    fixes: ['Added dynamic config propagation in StreamingETL.__init__()'],
    tags: ['bug', 'fix', 'perf'],
    filesCreated: 0, testsPassing: 33, rowsLoaded: 109000
  },
  {
    id: 7, date: '2026-06-08',
    title: 'The Library — Repository Goes Public',
    goal: 'Design advanced GitHub representation, add CI/CD, and push to GitHub',
    summary: 'The codebase found its public home. A GitHub Actions CI workflow was forged, CONTRIBUTING.md and SECURITY.md established governance, and the README was transformed with Mermaid sequence diagrams and performance benchmarks. The repository was pushed to github.com/VamsiReddy17/multi-agent-etl-console.',
    activities: [
      'Scanned repository for sensitive credentials (none found)',
      'Created .gitignore for .env, caches, logs, pid files',
      'Initialized Git repository and pushed to GitHub',
      'Added GitHub Actions CI workflow with pytest',
      'Created CONTRIBUTING.md and SECURITY.md',
      'Redesigned README with Mermaid diagrams and benchmarks'
    ],
    issues: ['Non-interactive terminal could not prompt for git credentials'],
    fixes: ['User ran initial git push in interactive terminal; credential helper cached'],
    tags: ['feature', 'feature'],
    filesCreated: 4, testsPassing: 33, rowsLoaded: 109000
  }
];

// ═══════════════════════════════════════════════════════════════════════════════
//  DATA: Bugs (The Bestiary)
// ═══════════════════════════════════════════════════════════════════════════════
const BUGS = [
  {
    id: 'BUG-001', title: 'Airflow API Connexion V3 Crash', severity: 'CRITICAL', status: 'fixed',
    discoveredIn: 'Session 2', fixedIn: 'Session 2', file: 'requirements.txt',
    description: 'The Airflow Webserver crashed on boot with TypeError: __init__() got an unexpected keyword argument \'skip_error_handlers\'. Connexion v3 removed this legacy argument that Airflow 2.5.3 depends on.',
    errorOutput: 'TypeError: __init__() got an unexpected keyword argument \'skip_error_handlers\'',
    rootCause: 'Unconstrained pip resolution installed connexion v3.3.0, which removed the skip_error_handlers parameter from its App constructor.',
    fix: 'Locked connexion[swagger]==2.14.2 in requirements.txt',
    lesson: 'Always lock major sub-dependencies to prevent transitive breaking changes in production environments.'
  },
  {
    id: 'BUG-002', title: 'Pendulum Timezone Module Incompatibility', severity: 'CRITICAL', status: 'fixed',
    discoveredIn: 'Session 2', fixedIn: 'Session 2', file: 'requirements.txt',
    description: 'All Airflow services threw TypeError: \'module\' object is not callable when attempting pendulum.tz.timezone("UTC") during datetime operations.',
    errorOutput: 'TypeError: \'module\' object is not callable',
    rootCause: 'Pendulum v3 restructured its timezone module, changing tz.timezone from a callable function to a module object. Airflow 2.5.3 calls it directly.',
    fix: 'Forced pendulum==2.1.2 across the dependency ecosystem',
    lesson: 'In legacy Airflow networks (v2.5.x), always lock timezone packages strictly to v2.'
  },
  {
    id: 'BUG-003', title: 'Flask-Session Namespace Shift', severity: 'CRITICAL', status: 'fixed',
    discoveredIn: 'Session 2', fixedIn: 'Session 2', file: 'requirements.txt',
    description: 'Database upgrades failed with ModuleNotFoundError: No module named \'flask_session.sessions\' due to internal file structure refactoring in flask-session v0.8.0.',
    errorOutput: 'ModuleNotFoundError: No module named \'flask_session.sessions\'',
    rootCause: 'flask-session v0.8.0 completely refactored its internal package layout, removing the flask_session.sessions submodule that Airflow imports.',
    fix: 'Locked flask-session==0.4.0 in the Airflow build environment',
    lesson: 'Lock supporting UI plugins to versions validated against your orchestrator.'
  },
  {
    id: 'BUG-004', title: 'SQLAlchemy v2.0 Breaking Changes', severity: 'CRITICAL', status: 'fixed',
    discoveredIn: 'Session 2', fixedIn: 'Session 2', file: 'requirements.txt',
    description: 'Docker builds failed because SQLAlchemy v2.0 is fundamentally incompatible with Airflow 2.5.3, which enforces a strict <2.0 upper bound.',
    errorOutput: 'ERROR: Cannot install sqlalchemy==2.0.0 — apache-airflow 2.5.3 depends on sqlalchemy<2.0',
    rootCause: 'SQLAlchemy 2.0 introduced breaking API changes incompatible with Airflow\'s ORM layer.',
    fix: 'Downgraded and pinned sqlalchemy==1.4.40 in requirements.txt',
    lesson: 'Check parent dependency bounds before updating helper ORMs.'
  },
  {
    id: 'BUG-005', title: 'Quality Agent Mock Test Short-Circuit', severity: 'HIGH', status: 'fixed',
    discoveredIn: 'Session 3', fixedIn: 'Session 3', file: 'tests/test_pipeline.py',
    description: 'Providing a small mock batch (2 valid, 1 bad) yielded a 33.3% anomaly rate, exceeding the 20% safety threshold, causing the Quality Agent to abort the entire pipeline run.',
    errorOutput: 'Quarantine rate 33.3% exceeds threshold 20.0% — aborting load',
    rootCause: 'The test used too few records (3 total), making a single bad record produce an artificially high quarantine percentage.',
    fix: 'Adjusted test dataset to 5 valid + 1 quarantined = 16.7% rate',
    lesson: 'Ensure test dataset sizes accurately reflect operational threshold rules.'
  },
  {
    id: 'BUG-006', title: 'Kafka Batch Size Propagation Defect', severity: 'HIGH', status: 'fixed',
    discoveredIn: 'Session 6', fixedIn: 'Session 6', file: 'pipelines/streaming_etl.py',
    description: 'The pipeline YAML config value batch_size: 2000 was completely ignored. The Kafka consumer silently defaulted to a batch size of 100, throttling throughput by 95%.',
    errorOutput: 'N/A — Silent performance degradation (no error thrown)',
    rootCause: 'StreamingETL.__init__() loaded YAML config but never mapped the properties to self.config before instantiating agents.',
    fix: 'Mapped YAML fields to PipelineConfig properties in StreamingETL.__init__() before agent creation',
    lesson: 'Always trace dynamic configuration properties through the full chain to ensure file settings reach all consumers.'
  },
  {
    id: 'BUG-007', title: 'ETL Loop Premature Termination', severity: 'MEDIUM', status: 'fixed',
    discoveredIn: 'Session 4', fixedIn: 'Session 4', file: 'pipelines/config/pipeline_config.yaml',
    description: 'The background streaming pipeline daemon automatically terminated after 10 loops, killing the metrics endpoint and stopping all data processing.',
    errorOutput: '[StreamingETL] 10 consecutive empty polls — stopping',
    rootCause: 'max_empty_polls was set to 10, causing clean loop exit after 10 empty Kafka pulls.',
    fix: 'Set max_empty_polls to 0 (infinite) in pipeline_config.yaml',
    lesson: 'For always-on streaming daemons, ensure termination guards are disabled or set to infinity.'
  },
  {
    id: 'BUG-008', title: 'Order Generator AttributeError Crash', severity: 'HIGH', status: 'fixed',
    discoveredIn: 'Session 5', fixedIn: 'Session 5', file: 'scripts/generate_orders.py',
    description: 'The order_generator container crashed immediately on startup with an AttributeError when trying to access the bad-rate command line argument.',
    errorOutput: 'AttributeError: \'Namespace\' object has no attribute \'bad\'',
    rootCause: 'Python argparse converts hyphenated argument names (--bad-rate) to underscored attributes (bad_rate), but the code referenced args.bad-rate which Python interprets as args.bad minus rate.',
    fix: 'Changed args.bad-rate to args.bad_rate in generate_orders.py',
    lesson: 'Always use underscored attribute names when accessing argparse arguments in Python.'
  },
  {
    id: 'BUG-009', title: 'Missing Container Environment Variables', severity: 'CRITICAL', status: 'fixed',
    discoveredIn: 'Session 2', fixedIn: 'Session 2', file: 'docker-compose.yml',
    description: 'Pipeline tasks inside Airflow containers failed to connect to Postgres and Kafka because environment variables defaulted to localhost instead of Docker network hostnames.',
    errorOutput: 'NoBrokersAvailable — connection refused at localhost:9092',
    rootCause: '.env file was excluded from Docker context by .dockerignore, and compose services didn\'t explicitly set POSTGRES_HOST and KAFKA_BROKER.',
    fix: 'Added explicit environment mappings: POSTGRES_HOST=postgres, KAFKA_BROKER=kafka:9092',
    lesson: 'Never rely on .env files inside Docker containers — set all critical env vars explicitly in docker-compose.yml.'
  }
];

// ═══════════════════════════════════════════════════════════════════════════════
//  DATA: Components (The Watchtower)
// ═══════════════════════════════════════════════════════════════════════════════
const INITIAL_COMPONENTS = [
  { id: 'zookeeper', name: 'Zookeeper Coordinator', type: 'infra', status: 'up', port: 2181, description: 'Manages and coordinates the Apache Kafka cluster.', memory: '48 MB', lag: '0ms' },
  { id: 'kafka', name: 'Apache Kafka Broker', type: 'infra', status: 'up', port: 9092, description: 'Highly-durable, high-throughput message streaming queue.', memory: '240 MB', lag: '2ms' },
  { id: 'redis', name: 'Redis Task Queue', type: 'infra', status: 'up', port: 6379, description: 'In-memory queue supporting Airflow\'s Celery Task Executors.', memory: '18 MB', lag: '0.1ms' },
  { id: 'postgres', name: 'PostgreSQL DW', type: 'infra', status: 'up', port: 5432, description: 'Target data warehouse hosting warehouse.order_events and audit logs.', memory: '85 MB', lag: '5ms' },
  { id: 'airflow_webserver', name: 'Airflow Web UI', type: 'orchestrator', status: 'up', port: 8080, description: 'Provides visual interface for DAG scheduling and system logs.', memory: '124 MB', lag: '0.5s' },
  { id: 'airflow_scheduler', name: 'Airflow Scheduler', type: 'orchestrator', status: 'up', port: '—', description: 'Triggers active streaming and batch DAG workflows.', memory: '98 MB', lag: '1.2s' },
  { id: 'airflow_worker', name: 'Airflow Worker', type: 'orchestrator', status: 'up', port: '—', description: 'Executes concurrent DAG worker tasks via Celery.', memory: '156 MB', lag: '0.8s' },
  { id: 'ingestion_agent', name: 'Kafka Ingestion Agent', type: 'agent', status: 'up', port: '—', description: 'Polls Kafka topic, deserializes JSON events with fault tolerance.', memory: '34 MB', lag: '28ms' },
  { id: 'transform_agent', name: 'Transform Agent', type: 'agent', status: 'up', port: '—', description: 'Type coerces, enriches metadata, and calculates order totals.', memory: '28 MB', lag: '14ms' },
  { id: 'quality_agent', name: 'Quality Validation Agent', type: 'agent', status: 'up', port: '—', description: 'Performs data rules checks, quarantining bad records.', memory: '32 MB', lag: '19ms' },
  { id: 'load_agent', name: 'PostgreSQL Load Agent', type: 'agent', status: 'up', port: '—', description: 'Performs high-performance bulk batch database insertions.', memory: '42 MB', lag: '45ms' },
  { id: 'prometheus', name: 'Prometheus Telemetry', type: 'monitor', status: 'up', port: 9090, description: 'Scrapes pipeline loop metrics from endpoint on port 8000.', memory: '52 MB', lag: '15s' },
  { id: 'grafana', name: 'Grafana Dashboard', type: 'monitor', status: 'up', port: 3000, description: 'Auto-provisioned analytics charts visualizing throughput.', memory: '64 MB', lag: '—' }
];

const PRE_DEPLOY_CHECKLIST = [
  { id: 'dep1', text: 'SQLAlchemy pinned to 1.4.40' },
  { id: 'dep2', text: 'Pendulum pinned to 2.1.2' },
  { id: 'dep3', text: 'Connexion pinned to 2.14.2' },
  { id: 'dep4', text: 'Flask-Session pinned to 0.4.0' },
  { id: 'limit1', text: 'Mock test anomaly rates kept under 20%' },
  { id: 'prop1', text: 'Configuration YAML values mapped to Agent instances' },
  { id: 'env1', text: 'Docker environment variables explicitly set (not from .env)' },
  { id: 'loop1', text: 'Streaming daemon max_empty_polls set to 0 (infinite)' }
];

// ═══════════════════════════════════════════════════════════════════════════════
//  DATA: Codex (Development Fable Entries)
// ═══════════════════════════════════════════════════════════════════════════════
const CODEX_ENTRIES = [
  {
    title: 'Prologue — The Empty Scaffold',
    date: 'Before Session 1',
    text: 'The project began as a skeleton — Docker Compose infrastructure in place, but zero application code. No agents, no pipelines, no tests. Just the promise of what a multi-agent ETL system could become, waiting in the bones of postgres, kafka, and airflow containers.',
    quote: '"In the beginning there was infrastructure, and infrastructure was without form, and void."',
    milestone: null
  },
  {
    title: 'Chapter I — The Four Agents',
    date: '2026-05-20',
    text: 'Four agents were forged in a single session. The Kafka Ingestion Agent to listen, the Transform Agent to shape, the Quality Agent to judge, and the Postgres Load Agent to persist. Each was given a strict JSON communication protocol — the language they would share to pass data between stages. A streaming orchestrator was built to bind them together, and Airflow DAGs were written to schedule their work.',
    quote: '"Each agent knows only its task. Together, they know the pipeline."',
    milestone: '26 files created from scratch'
  },
  {
    title: 'Chapter II — The Dependency Wars',
    date: '2026-05-20',
    text: 'The first docker-compose up revealed a battlefield. Six critical dependency conflicts erupted simultaneously. Connexion v3 had silently removed a parameter Airflow needed. Pendulum v3 changed how timezones worked. Flask-Session restructured its modules. SQLAlchemy v2 broke everything. Each was hunted down, diagnosed, and pinned to a compatible version. By the end, 31 tests passed cleanly.',
    quote: '"The hardest bugs are the ones your dependencies introduce when you aren\'t looking."',
    milestone: '6 critical bugs fixed, 31 tests passing'
  },
  {
    title: 'Chapter III — The Eye Opens',
    date: '2026-05-21',
    text: 'With the pipeline stable, it was time to see inside it. Prometheus and Grafana were woven into the Docker stack. Five custom metrics were instrumented directly into the streaming orchestrator — pipeline runs, rows processed, rows quarantined, stage durations, and batch latencies. A pre-built Grafana dashboard materialized automatically on port 3000, its panels ready to visualize throughput.',
    quote: '"You cannot optimize what you cannot observe."',
    milestone: 'Full observability stack operational'
  },
  {
    title: 'Chapter IV — The Infinite Loop',
    date: '2026-05-21',
    text: 'A subtle defect emerged: the streaming daemon kept dying. After 10 empty Kafka polls, it would gracefully terminate — taking the metrics endpoint with it. The fix was simple but the lesson was deep: always-on services must have their safety guards configured for perpetuity, not convenience.',
    quote: '"A daemon that stops is not a daemon at all."',
    milestone: 'Prometheus target confirmed UP'
  },
  {
    title: 'Chapter V — The Flood',
    date: '2026-05-21',
    text: 'A continuous order generator was unleashed: 250 events per second, each a simulated e-commerce order with a 10% anomaly injection rate. But the generator crashed immediately — args.bad-rate vs args.bad_rate, a classic Python argparse trap. Once fixed, data poured through the pipeline. The database grew from 33 rows to 81, then to thousands. The pipeline had proven it could swim.',
    quote: '"The first thousand rows teach you more than the first hundred lines of code."',
    milestone: '7,280+ rows loaded at 280 rows/sec'
  },
  {
    title: 'Chapter VI — The Crucible',
    date: '2026-05-21',
    text: 'The final performance barrier was invisible. batch_size: 2000 was written in the YAML config, but the agents received 100. The StreamingETL orchestrator loaded the YAML but never propagated its values to the agent configuration objects. A single code change — dynamic property mapping in __init__() — unleashed the full power. 109,000+ rows in minutes. Peak throughput: 1,000 messages per second.',
    quote: '"Configuration that isn\'t propagated is configuration that doesn\'t exist."',
    milestone: '109,000+ rows loaded, 1,000 msg/s peak'
  },
  {
    title: 'Chapter VII — The Library',
    date: '2026-06-08',
    text: 'The codebase left the developer\'s machine and entered the public world. Git was initialized, sensitive credentials were audited (none found), and the repository was pushed to GitHub. A CI workflow was added to run tests on every push. CONTRIBUTING.md and SECURITY.md established governance. The README was transformed into a living document with Mermaid sequence diagrams and performance benchmarks.',
    quote: '"Code without a home is code without a future."',
    milestone: 'Repository published to GitHub'
  }
];

// ═══════════════════════════════════════════════════════════════════════════════
//  MAIN APP COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════
export default function App() {
  const [activeTab, setActiveTab] = useState('chronicle');
  const [liveMode, setLiveMode] = useState(false);
  const [components, setComponents] = useState(INITIAL_COMPONENTS);
  const [selectedComp, setSelectedComp] = useState(INITIAL_COMPONENTS[0]);

  // Chronicle expanded chapter
  const [expandedChapter, setExpandedChapter] = useState(null);

  // Bestiary filter
  const [bugFilter, setBugFilter] = useState('ALL');
  const [expandedBug, setExpandedBug] = useState(null);

  // Simulation controls
  const [isGenerating, setIsGenerating] = useState(true);
  const [streamVelocity, setStreamVelocity] = useState(250);
  const [anomalyRate, setAnomalyRate] = useState(10.2);

  // System logs
  const [logs, setLogs] = useState([
    { id: 1, type: 'info', text: '⟐ Initializing multi-agent telemetry stream...' },
    { id: 2, type: 'success', text: '✦ Connected to Docker socket: unix:///var/run/docker.sock' },
    { id: 3, type: 'info', text: '⟐ Active Kafka topic brokers at localhost:9092' },
    { id: 4, type: 'success', text: '✦ E2E bootstrap complete — System fully operational' }
  ]);
  const terminalRef = useRef(null);

  // Kafka lag
  const [kafkaLag, setKafkaLag] = useState(0);

  // Quarantine records
  const [quarantineRecords, setQuarantineRecords] = useState([
    { id: 'REC-904', timestamp: '11:10:04', agent: 'QualityAgent', error: 'Negative value on total_amount', payload: '{\n  "order_id": 84920,\n  "customer_id": "cust_29402",\n  "total_amount": -12.50\n}' },
    { id: 'REC-908', timestamp: '11:12:15', agent: 'QualityAgent', error: 'Missing field: currency code', payload: '{\n  "order_id": 38104,\n  "customer_id": "cust_93014",\n  "total_amount": 89.99,\n  "currency": null\n}' },
    { id: 'REC-911', timestamp: '11:15:32', agent: 'QualityAgent', error: 'Character overflow on country field', payload: '{\n  "order_id": 74910,\n  "total_amount": 412.00,\n  "country": "OVERFLOW_FIELD"\n}' }
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
    'warehouse.pipeline_execution': [
      { id: 'run_683', dag: 'streaming_ingestion', tasks: '4/4', state: 'Success', latency: '128ms' },
      { id: 'run_684', dag: 'streaming_ingestion', tasks: '4/4', state: 'Success', latency: '135ms' },
      { id: 'run_685', dag: 'streaming_ingestion', tasks: '3/4', state: 'Failed', latency: '42ms' },
      { id: 'run_686', dag: 'streaming_ingestion', tasks: '4/4', state: 'Success', latency: '114ms' }
    ]
  });

  // Pipeline metrics
  const [metrics, setMetrics] = useState({
    totalRuns: 33, successRuns: 33,
    processedIngest: 66000, processedLoad: 59271,
    quarantined: 6729, quarantineRate: 10.19,
    loadedCount: 249444, ingestRate: 250, avgLatency: 11.2,
    stageDurations: { ingestion: 0.13, transform: 0.01, quality: 0.006, load: 0.19 }
  });

  // Checklist
  const [checklist, setChecklist] = useState(
    PRE_DEPLOY_CHECKLIST.map(item => ({ ...item, checked: true }))
  );

  // Particles for constellation
  const [particles, setParticles] = useState([]);
  const particleIdRef = useRef(0);

  // ═══════════════════════════════════════════════════════════════════════════
  //  PHASE 3 — Observatory Features
  // ═══════════════════════════════════════════════════════════════════════════

  // Command Palette (Cmd+K)
  const [cmdOpen, setCmdOpen] = useState(false);
  const [cmdQuery, setCmdQuery] = useState('');
  const cmdInputRef = useRef(null);
  const [cmdActiveIdx, setCmdActiveIdx] = useState(0);

  // Toast Notifications
  const [toasts, setToasts] = useState([]);
  const toastIdRef = useRef(0);

  // Sparkline History
  const [sparkHistory, setSparkHistory] = useState({
    loaded: Array(20).fill(0).map(() => Math.random() * 60 + 40),
    throughput: Array(20).fill(0).map(() => Math.random() * 40 + 60),
    quarantine: Array(20).fill(0).map(() => Math.random() * 30 + 10),
    runs: Array(20).fill(0).map(() => Math.random() * 50 + 50)
  });

  // Search filters
  const [chronicleSearch, setChronicleSearch] = useState('');
  const [bestiarySearch, setBestiarySearch] = useState('');

  // Toast helper
  const addToast = useCallback((type, text) => {
    const id = toastIdRef.current++;
    setToasts(prev => [...prev, { id, type, text }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500);
  }, []);

  // Update sparkline history on metric changes
  useEffect(() => {
    if (!isGenerating) return;
    const intervalId = setInterval(() => {
      setSparkHistory(prev => ({
        loaded: [...prev.loaded.slice(1), Math.min(100, (metrics.loadedCount / 3000) % 100)],
        throughput: [...prev.throughput.slice(1), Math.min(100, (metrics.ingestRate / 5) % 100)],
        quarantine: [...prev.quarantine.slice(1), Math.min(100, metrics.quarantineRate * 5)],
        runs: [...prev.runs.slice(1), Math.min(100, (metrics.successRuns % 50) * 2)]
      }));
    }, 2000);
    return () => clearInterval(intervalId);
  }, [isGenerating, metrics.loadedCount, metrics.ingestRate, metrics.quarantineRate, metrics.successRuns]);

  // Toggle service status
  const toggleComponentStatus = (id) => {
    setComponents(prev => prev.map(comp => {
      if (comp.id === id) {
        const newStatus = comp.status === 'up' ? 'down' : 'up';
        const timestamp = new Date().toLocaleTimeString();
        setLogs(logPrev => [...logPrev, {
          id: Date.now(), type: newStatus === 'up' ? 'success' : 'error',
          text: `[${timestamp}] Service '${comp.name}' toggled ${newStatus.toUpperCase()}`
        }]);
        return { ...comp, status: newStatus };
      }
      return comp;
    }));
  };

  // WebSocket for live mode
  useEffect(() => {
    if (!liveMode) return;
    let socket, reconnectTimeout;
    const connect = () => {
      socket = new WebSocket("ws://localhost:8085/ws");
      socket.onopen = () => {
        setLogs(prev => [...prev, { id: Date.now(), type: 'success', text: `[${new Date().toLocaleTimeString()}] ✦ Live WebSocket connected at ws://localhost:8085/ws` }]);
      };
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.metrics) setMetrics(prev => ({ ...prev, ...payload.metrics }));
          if (payload.logs?.length > 0) setLogs(payload.logs);
          if (payload.quarantine) setQuarantineRecords(payload.quarantine);
          if (payload.db_records) setDbRecords(payload.db_records);
        } catch (err) { console.error("[WS] Parse error:", err); }
      };
      socket.onclose = () => { reconnectTimeout = setTimeout(connect, 3000); };
      socket.onerror = () => { socket.close(); };
    };
    connect();
    return () => { if (socket) socket.close(); if (reconnectTimeout) clearTimeout(reconnectTimeout); };
  }, [liveMode]);

  // Simulation loop
  useEffect(() => {
    let intervalId;
    if (!liveMode && isGenerating) {
      intervalId = setInterval(() => {
        const isIngestUp = components.find(c => c.id === 'ingestion_agent')?.status === 'up';
        const isKafkaUp = components.find(c => c.id === 'kafka')?.status === 'up';
        const timestamp = new Date().toLocaleTimeString();

        if (!isKafkaUp) {
          setLogs(prev => [...prev, { id: Date.now(), type: 'error', text: `[${timestamp}] ⚠ CRITICAL — Broker failure at localhost:9092` }].slice(-50));
          setMetrics(prev => ({ ...prev, ingestRate: 0 }));
          setComponents(prev => prev.map(c => c.type === 'agent' ? { ...c, status: 'pending' } : c));
          return;
        }
        setComponents(prev => prev.map(c => c.type === 'agent' && c.status === 'pending' ? { ...c, status: 'up' } : c));

        if (!isIngestUp) {
          const lagGrowth = Math.round(streamVelocity * 2.0);
          setKafkaLag(prev => prev + lagGrowth);
          setLogs(prev => [...prev, { id: Date.now(), type: 'warning', text: `[${timestamp}] Ingest Agent down. Backlog: +${lagGrowth} records` }].slice(-50));
          return;
        }

        let batchSize = Math.round(streamVelocity * 2.0);
        let isBurst = false;
        if (kafkaLag > 0) {
          isBurst = true;
          const burstSize = Math.min(kafkaLag, batchSize * 3);
          batchSize += burstSize;
          setKafkaLag(prev => Math.max(0, prev - burstSize));
        }

        const badCount = Math.round(batchSize * (anomalyRate / 100));
        const goodCount = batchSize - badCount;

        setMetrics(prev => {
          const newProcessed = prev.processedIngest + batchSize;
          const newQuarantined = prev.quarantined + badCount;
          const newLoaded = prev.processedLoad + goodCount;
          const newRate = parseFloat(((newQuarantined / newProcessed) * 100).toFixed(2));
          return {
            ...prev, processedIngest: newProcessed, quarantined: newQuarantined,
            processedLoad: newLoaded, loadedCount: prev.loadedCount + goodCount,
            quarantineRate: newRate, totalRuns: prev.totalRuns + 1,
            successRuns: prev.successRuns + 1, ingestRate: isBurst ? streamVelocity * 2 : streamVelocity
          };
        });

        const newLogs = [
          { id: Date.now() + 1, type: 'info', text: `[${timestamp}] ⟐ Kafka:orders polled. ${isBurst ? '⚡ BURST' : 'Normal'} batch: ${batchSize}` },
          { id: Date.now() + 2, type: 'success', text: `[${timestamp}] ✦ Ingest → ${batchSize} events parsed` }
        ];
        if (badCount > 0) {
          newLogs.push({ id: Date.now() + 3, type: anomalyRate > 20 ? 'error' : 'warning', text: `[${timestamp}] ⚑ Quality quarantined ${badCount} records (${anomalyRate}%)` });
          const rId = Math.floor(Math.random() * 90000) + 10000;
          setQuarantineRecords(prev => [{ id: `REC-${rId}`, timestamp, agent: 'QualityAgent', error: 'Missing field: currency', payload: `{\n  "order_id": ${rId},\n  "total_amount": ${(Math.random() * 200).toFixed(2)}\n}` }, ...prev].slice(0, 10));
        }
        newLogs.push({ id: Date.now() + 4, type: 'success', text: `[${timestamp}] ✦ Load → ${goodCount} rows saved to PostgreSQL` });
        setLogs(prev => [...prev, ...newLogs].slice(-50));

        // Update db records
        const evt = { id: `evt_${Math.floor(Math.random() * 90000) + 10000}`, customer: `cust_${Math.floor(Math.random() * 90000) + 10000}`, total: `$${(Math.random() * 500 + 10).toFixed(2)}`, status: Math.random() * 100 >= anomalyRate ? 'Passed' : 'Quarantined', time: timestamp };
        const run = { id: `run_${Math.floor(Math.random() * 900) + 100}`, dag: 'streaming_ingestion', tasks: '4/4', state: 'Success', latency: `${Math.floor(Math.random() * 100) + 80}ms` };
        setDbRecords(prev => ({
          'warehouse.order_events': [evt, ...prev['warehouse.order_events']].slice(0, 5),
          'warehouse.pipeline_execution': [run, ...prev['warehouse.pipeline_execution']].slice(0, 5)
        }));
      }, 2000);
    }
    return () => { if (intervalId) clearInterval(intervalId); };
  }, [liveMode, isGenerating, streamVelocity, anomalyRate, components, kafkaLag]);

  // Particle emitter
  useEffect(() => {
    let intervalId;
    const isUp = components.find(c => c.id === 'ingestion_agent')?.status === 'up' && components.find(c => c.id === 'kafka')?.status === 'up';
    if (isGenerating && isUp) {
      intervalId = setInterval(() => {
        const isBad = Math.random() * 100 < anomalyRate;
        setParticles(prev => [...prev, { id: particleIdRef.current++, step: 0, isBad }]);
      }, Math.max(150, 1000 - (streamVelocity * 0.8)));
    }
    return () => { if (intervalId) clearInterval(intervalId); };
  }, [isGenerating, streamVelocity, anomalyRate, components]);

  // Particle stepper
  useEffect(() => {
    let intervalId;
    if (isGenerating) {
      intervalId = setInterval(() => {
        setParticles(prev => prev.map(p => ({ ...p, step: p.step + 1 })).filter(p => p.step <= 4));
      }, 900);
    }
    return () => { if (intervalId) clearInterval(intervalId); };
  }, [isGenerating]);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current) terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
  }, [logs]);

  // Focus cmd input when palette opens
  useEffect(() => {
    if (cmdOpen && cmdInputRef.current) {
      cmdInputRef.current.focus();
      setCmdQuery('');
      setCmdActiveIdx(0);
    }
  }, [cmdOpen]);

  // Keyboard shortcuts
  useEffect(() => {
    const tabKeys = ['chronicle', 'bestiary', 'codex', 'forge', 'constellation', 'watchtower', 'quarantine'];
    const handler = (e) => {
      // Cmd+K or Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCmdOpen(prev => !prev);
        return;
      }
      // Escape
      if (e.key === 'Escape' && cmdOpen) {
        setCmdOpen(false);
        return;
      }
      // Number keys 1-7 for tab switching (only when no input focused)
      if (!cmdOpen && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) {
        const num = parseInt(e.key);
        if (num >= 1 && num <= 7) {
          setActiveTab(tabKeys[num - 1]);
          addToast('info', `Switched to ${tabKeys[num - 1].charAt(0).toUpperCase() + tabKeys[num - 1].slice(1)}`);
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [cmdOpen, addToast]);

  // Command palette search index
  const cmdItems = [
    // Tabs
    ...['chronicle', 'bestiary', 'codex', 'forge', 'constellation', 'watchtower', 'quarantine'].map((id, i) => ({
      type: 'tab', id, label: `Go to The ${id.charAt(0).toUpperCase() + id.slice(1)}`, shortcut: `${i + 1}`,
      icon: [BookOpen, Bug, Award, Activity, Layers, Eye, AlertTriangle][i]
    })),
    // Actions
    { type: 'action', id: 'toggle-sim', label: isGenerating ? 'Pause Simulation' : 'Resume Simulation', icon: isGenerating ? Pause : Play },
    { type: 'action', id: 'toggle-live', label: liveMode ? 'Switch to Simulation Mode' : 'Switch to Live Mode', icon: Heart },
    // Sessions
    ...SESSIONS.map(s => ({ type: 'session', id: `session-${s.id}`, label: s.title, meta: s.date, icon: BookOpen })),
    // Bugs
    ...BUGS.map(b => ({ type: 'bug', id: b.id, label: `${b.id}: ${b.title}`, meta: b.severity, icon: Bug })),
    // Components
    ...INITIAL_COMPONENTS.map(c => ({ type: 'service', id: c.id, label: c.name, meta: `port ${c.port}`, icon: Server }))
  ];

  const filteredCmdItems = cmdQuery.trim() === ''
    ? cmdItems.slice(0, 12)
    : cmdItems.filter(item => item.label.toLowerCase().includes(cmdQuery.toLowerCase())).slice(0, 12);

  const executeCmdItem = (item) => {
    setCmdOpen(false);
    if (item.type === 'tab') { setActiveTab(item.id); addToast('info', `Navigated to The ${item.id.charAt(0).toUpperCase() + item.id.slice(1)}`); }
    else if (item.type === 'action' && item.id === 'toggle-sim') { setIsGenerating(p => !p); addToast('info', isGenerating ? 'Simulation paused' : 'Simulation resumed'); }
    else if (item.type === 'action' && item.id === 'toggle-live') { setLiveMode(p => !p); addToast('info', liveMode ? 'Switched to Simulation' : 'Switched to Live'); }
    else if (item.type === 'session') { setActiveTab('chronicle'); setExpandedChapter(parseInt(item.id.split('-')[1])); addToast('info', `Opened ${item.label}`); }
    else if (item.type === 'bug') { setActiveTab('bestiary'); setExpandedBug(item.id); addToast('info', `Opened ${item.id}`); }
    else if (item.type === 'service') { setActiveTab('watchtower'); setSelectedComp(INITIAL_COMPONENTS.find(c => c.id === item.id)); addToast('info', `Viewing ${item.label}`); }
  };

  // Compute system health
  const healthyCount = components.filter(c => c.status === 'up').length;
  const systemHealth = healthyCount === components.length ? 'healthy' : healthyCount > components.length * 0.7 ? 'degraded' : 'critical';

  // Filtered bugs (with search)
  const filteredBugs = (bugFilter === 'ALL' ? BUGS : BUGS.filter(b => b.severity === bugFilter))
    .filter(b => bestiarySearch === '' || b.title.toLowerCase().includes(bestiarySearch.toLowerCase()) || b.description.toLowerCase().includes(bestiarySearch.toLowerCase()));

  // Filtered sessions (with search)
  const filteredSessions = SESSIONS.filter(s => chronicleSearch === '' || s.title.toLowerCase().includes(chronicleSearch.toLowerCase()) || s.summary.toLowerCase().includes(chronicleSearch.toLowerCase()));

  // Node positions for constellation
  const nodePositions = [
    { left: '8%', label: 'Kafka', cls: 'source' },
    { left: '27%', label: 'Ingest', cls: 'ingest' },
    { left: '46%', label: 'Transform', cls: 'transform' },
    { left: '65%', label: 'Quality', cls: 'quality' },
    { left: '84%', label: 'Postgres', cls: 'load' },
  ];

  // ═════════════════════════════════════════════════════════════════════════════
  //  NAVIGATION CONFIG
  // ═════════════════════════════════════════════════════════════════════════════
  const navItems = [
    { section: 'NARRATIVE' },
    { id: 'chronicle', label: 'The Chronicle', icon: <BookOpen size={18} />, kbd: '1' },
    { id: 'bestiary', label: 'The Bestiary', icon: <Bug size={18} />, badge: BUGS.length, kbd: '2' },
    { id: 'codex', label: 'The Codex', icon: <Award size={18} />, kbd: '3' },
    { section: 'OPERATIONS' },
    { id: 'forge', label: 'The Forge', icon: <Activity size={18} />, kbd: '4' },
    { id: 'constellation', label: 'The Constellation', icon: <Layers size={18} />, kbd: '5' },
    { id: 'watchtower', label: 'The Watchtower', icon: <Eye size={18} />, kbd: '6' },
    { id: 'quarantine', label: 'The Quarantine', icon: <AlertTriangle size={18} />, badge: quarantineRecords.length, kbd: '7' },
  ];

  // ═════════════════════════════════════════════════════════════════════════════
  //  RENDER
  // ═════════════════════════════════════════════════════════════════════════════
  return (
    <div className="fable-app">
      {/* ──── SIDEBAR ──── */}
      <aside className="fable-sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">
            <Zap size={20} color="white" />
          </div>
          <div className="brand-title">The Fable</div>
          <div className="brand-subtitle">Multi-Agent ETL Chronicle</div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item, i) => {
            if (item.section) {
              return <div key={i} className="nav-section-label">{item.section}</div>;
            }
            return (
              <div
                key={item.id}
                className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                {item.icon}
                <span>{item.label}</span>
                {item.badge > 0 && <span className="nav-badge">{item.badge}</span>}
                {item.kbd && <span className="kbd-hint">{item.kbd}</span>}
              </div>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span className={`status-orb ${systemHealth}`}></span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.78rem' }}>
              {systemHealth === 'healthy' ? 'ALL SYSTEMS NOMINAL' : systemHealth === 'degraded' ? 'DEGRADED' : 'CRITICAL'}
            </span>
          </div>
          <div style={{ color: 'var(--text-muted)' }}>{healthyCount}/{components.length} services up</div>
          <div style={{ color: 'var(--text-muted)', marginTop: 2 }}>
            {liveMode ? 'Live Telemetry Mode' : 'Simulation Mode'}
          </div>
        </div>
      </aside>

      {/* ──── MAIN ──── */}
      <main className="fable-main">
        <header className="fable-topbar">
          <div className="topbar-title">
            {activeTab === 'chronicle' && '📜 The Chronicle'}
            {activeTab === 'bestiary' && '🐛 The Bestiary'}
            {activeTab === 'codex' && '📖 The Codex'}
            {activeTab === 'forge' && '⚡ The Forge'}
            {activeTab === 'constellation' && '✨ The Constellation'}
            {activeTab === 'watchtower' && '🗼 The Watchtower'}
            {activeTab === 'quarantine' && '🔒 The Quarantine'}
          </div>
          <div className="topbar-controls">
            <div
              className="mode-pill"
              onClick={() => setCmdOpen(true)}
              style={{ cursor: 'pointer', gap: 6 }}
            >
              <Command size={12} />
              <span style={{ fontSize: '0.72rem' }}>⌘K</span>
            </div>
            <div
              className={`mode-pill ${liveMode ? 'active' : ''}`}
              onClick={() => setLiveMode(!liveMode)}
            >
              <span className={`status-orb ${liveMode ? 'healthy' : 'degraded'}`} style={{ animation: 'none', width: 6, height: 6 }}></span>
              {liveMode ? 'Live' : 'Simulation'}
            </div>
            <Heart size={18} style={{ color: '#ec4899' }} />
          </div>
        </header>

        <div className="fable-workspace">

          {/* ════════════════════════════════════════════════════════════════════
              TAB 1: THE CHRONICLE
          ════════════════════════════════════════════════════════════════════ */}
          {activeTab === 'chronicle' && (
            <>
              <div className="chronicle-hero">
                <h1>The Chronicle</h1>
                <p>
                  Every session of the Multi-Agent ETL Pipeline, told as chapters in a development saga — from empty scaffold to 109,000+ rows at 1,000 msg/s.
                </p>
                <div className="chronicle-stats">
                  <div className="chronicle-stat">
                    <div className="chronicle-stat-value">7</div>
                    <div className="chronicle-stat-label">Sessions</div>
                  </div>
                  <div className="chronicle-stat">
                    <div className="chronicle-stat-value">9</div>
                    <div className="chronicle-stat-label">Bugs Fixed</div>
                  </div>
                  <div className="chronicle-stat">
                    <div className="chronicle-stat-value">109K+</div>
                    <div className="chronicle-stat-label">Rows Loaded</div>
                  </div>
                  <div className="chronicle-stat">
                    <div className="chronicle-stat-value">33</div>
                    <div className="chronicle-stat-label">Tests Passing</div>
                  </div>
                </div>
              </div>

              <div className="search-bar">
                <Search size={16} />
                <input
                  placeholder="Search sessions by title or summary..."
                  value={chronicleSearch}
                  onChange={e => setChronicleSearch(e.target.value)}
                />
              </div>

              <div className="timeline">
                {filteredSessions.map((session) => (
                  <div key={session.id} className="timeline-chapter">
                    <div className="timeline-dot"></div>
                    <div
                      className={`chapter-card ${expandedChapter === session.id ? 'expanded' : ''}`}
                      onClick={() => setExpandedChapter(expandedChapter === session.id ? null : session.id)}
                    >
                      <div className="chapter-meta">
                        <span className="chapter-number">Session {session.id}</span>
                        <span className="chapter-date">{session.date}</span>
                        <span style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>
                          {expandedChapter === session.id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        </span>
                      </div>
                      <div className="chapter-title">{session.title}</div>
                      <div className="chapter-summary">{session.summary}</div>
                      <div className="chapter-tags">
                        {session.tags.map((tag, i) => (
                          <span key={i} className={`chapter-tag tag-${tag}`}>{tag}</span>
                        ))}
                        {session.issues.length > 0 && (
                          <span className="chapter-tag tag-bug">{session.issues.length} issue{session.issues.length > 1 ? 's' : ''}</span>
                        )}
                      </div>

                      {expandedChapter === session.id && (
                        <div className="chapter-details">
                          <div className="chapter-detail-section">
                            <div className="chapter-detail-label">🔍 Activities</div>
                            <ul className="chapter-detail-list">
                              {session.activities.map((a, i) => <li key={i}>{a}</li>)}
                            </ul>
                          </div>
                          {session.issues.length > 0 && (
                            <div className="chapter-detail-section">
                              <div className="chapter-detail-label">⚠️ Issues Encountered</div>
                              <ul className="chapter-detail-list">
                                {session.issues.map((iss, i) => <li key={i} style={{ color: 'var(--crimson-glow)' }}>{iss}</li>)}
                              </ul>
                            </div>
                          )}
                          {session.fixes.length > 0 && (
                            <div className="chapter-detail-section">
                              <div className="chapter-detail-label">🔧 Fixes Applied</div>
                              <ul className="chapter-detail-list">
                                {session.fixes.map((f, i) => <li key={i} style={{ color: 'var(--emerald-glow)' }}>{f}</li>)}
                              </ul>
                            </div>
                          )}
                          <div style={{ display: 'flex', gap: 24, marginTop: 12, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                            {session.filesCreated > 0 && <span>📄 {session.filesCreated} files created</span>}
                            {session.testsPassing > 0 && <span>✅ {session.testsPassing} tests passing</span>}
                            {session.rowsLoaded > 0 && <span>📊 {session.rowsLoaded.toLocaleString()} rows loaded</span>}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* ════════════════════════════════════════════════════════════════════
              TAB 2: THE BESTIARY
          ════════════════════════════════════════════════════════════════════ */}
          {activeTab === 'bestiary' && (
            <>
              <div className="bestiary-header">
                <h2>The Bestiary</h2>
                <p>Every bug encountered, diagnosed, and conquered — with root cause analysis, fixes, and lessons learned.</p>
              </div>
              <div className="bestiary-filters">
                <div className="search-bar" style={{ marginBottom: 12, flex: 1 }}>
                  <Search size={16} />
                  <input
                    placeholder="Search bugs by title or description..."
                    value={bestiarySearch}
                    onChange={e => setBestiarySearch(e.target.value)}
                  />
                </div>
              </div>

              <div className="bestiary-filters">
                {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(f => (
                  <button
                    key={f}
                    className={`filter-chip ${bugFilter === f ? 'active' : ''}`}
                    onClick={() => setBugFilter(f)}
                  >
                    {f} {f !== 'ALL' && `(${BUGS.filter(b => b.severity === f).length})`}
                  </button>
                ))}
              </div>

              <div className="bestiary-grid">
                {filteredBugs.map(bug => (
                  <div
                    key={bug.id}
                    className={`bug-card severity-${bug.severity.toLowerCase()}`}
                    onClick={() => setExpandedBug(expandedBug === bug.id ? null : bug.id)}
                  >
                    <div className="bug-card-header">
                      <span className="bug-id">{bug.id}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className={`severity-badge ${bug.severity.toLowerCase()}`}>{bug.severity}</span>
                        <span style={{ fontSize: '0.68rem', color: 'var(--emerald)', fontWeight: 600 }}>✓ FIXED</span>
                      </div>
                    </div>
                    <div className="bug-title">{bug.title}</div>
                    <div className="bug-description">{bug.description}</div>

                    {expandedBug === bug.id && (
                      <div className="bug-fix-section">
                        <div className="bug-fix-block">
                          <div className="bug-fix-label"><Terminal size={12} /> Error Output</div>
                          <div className="bug-fix-code">{bug.errorOutput}</div>
                        </div>
                        <div className="bug-fix-block">
                          <div className="bug-fix-label"><Eye size={12} /> Root Cause</div>
                          <div className="bug-fix-text">{bug.rootCause}</div>
                        </div>
                        <div className="bug-fix-block">
                          <div className="bug-fix-label"><Wrench size={12} /> Fix Applied</div>
                          <div className="bug-fix-code">{bug.fix}</div>
                        </div>
                        <div className="bug-lesson">
                          💡 <strong>Lesson:</strong> {bug.lesson}
                        </div>
                        <div className="bug-meta-row">
                          <span className="bug-meta"><Clock size={12} /> Discovered: {bug.discoveredIn}</span>
                          <span className="bug-meta"><CheckCircle size={12} /> Fixed: {bug.fixedIn}</span>
                          <span className="bug-meta"><Server size={12} /> {bug.file}</span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}

          {/* ════════════════════════════════════════════════════════════════════
              TAB 3: THE FORGE (Live Metrics)
          ════════════════════════════════════════════════════════════════════ */}
          {activeTab === 'forge' && (
            <>
              <div className="section-head">
                <h2>The Forge</h2>
                <p>Real-time pipeline performance metrics, throughput rates, and stage execution durations.</p>
              </div>

              {/* Metrics Grid */}
              <div className="metrics-grid">
                <div className="metric-tile blue">
                  <div className="metric-tile-label">
                    <span>Loaded DB Events</span>
                    <Database size={16} style={{ color: 'var(--sapphire)' }} />
                  </div>
                  <div className="metric-tile-value" style={{ color: 'var(--sapphire-glow)' }}>
                    {metrics.loadedCount.toLocaleString()}
                  </div>
                  <div className="metric-tile-sub">
                    <TrendingUp size={12} className="up" />
                    <span className="up">PostgreSQL warehouse</span>
                  </div>
                  <div className="sparkline-container">
                    {sparkHistory.loaded.map((v, i) => (
                      <div key={i} className="sparkline-bar blue" style={{ height: `${v}%` }} />
                    ))}
                  </div>
                </div>

                <div className="metric-tile green">
                  <div className="metric-tile-label">
                    <span>Throughput Rate</span>
                    <Cpu size={16} style={{ color: 'var(--emerald)' }} />
                  </div>
                  <div className="metric-tile-value" style={{ color: 'var(--emerald-glow)' }}>
                    {metrics.ingestRate} <span style={{ fontSize: '0.9rem', fontWeight: 400 }}>evt/s</span>
                  </div>
                  <div className="metric-tile-sub">
                    <Activity size={12} className="up" />
                    <span>Peak: 1,000 evt/s</span>
                  </div>
                  <div className="sparkline-container">
                    {sparkHistory.throughput.map((v, i) => (
                      <div key={i} className="sparkline-bar green" style={{ height: `${v}%` }} />
                    ))}
                  </div>
                </div>

                <div className="metric-tile red">
                  <div className="metric-tile-label">
                    <span>Quarantine Rate</span>
                    <AlertTriangle size={16} style={{ color: 'var(--crimson)' }} />
                  </div>
                  <div className="metric-tile-value" style={{ color: 'var(--crimson-glow)' }}>
                    {metrics.quarantineRate}%
                  </div>
                  <div className="metric-tile-sub">
                    <ShieldCheck size={12} />
                    <span>Safety limit: 20.0%</span>
                  </div>
                  <div className="sparkline-container">
                    {sparkHistory.quarantine.map((v, i) => (
                      <div key={i} className="sparkline-bar red" style={{ height: `${v}%` }} />
                    ))}
                  </div>
                </div>

                <div className="metric-tile amber">
                  <div className="metric-tile-label">
                    <span>Pipeline Runs</span>
                    <RefreshCw size={16} style={{ color: 'var(--amber)' }} />
                  </div>
                  <div className="metric-tile-value" style={{ color: 'var(--amber)' }}>
                    {metrics.successRuns}
                  </div>
                  <div className="metric-tile-sub">
                    <span>Batch size: 2,000</span>
                  </div>
                  <div className="sparkline-container">
                    {sparkHistory.runs.map((v, i) => (
                      <div key={i} className="sparkline-bar amber" style={{ height: `${v}%` }} />
                    ))}
                  </div>
                </div>
              </div>

              {/* Two-Column: Stages + Controls */}
              <div className="two-col">
                <div className="glass-card">
                  <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 600, marginBottom: 20, color: 'var(--text-primary)' }}>
                    Stage Execution Durations
                  </h3>
                  <div className="stage-bars">
                    {[
                      { name: 'Ingestion', val: metrics.stageDurations.ingestion, max: 0.2, cls: 'blue' },
                      { name: 'Transform', val: metrics.stageDurations.transform, max: 0.2, cls: 'violet' },
                      { name: 'Quality', val: metrics.stageDurations.quality, max: 0.2, cls: 'amber' },
                      { name: 'Load', val: metrics.stageDurations.load, max: 0.2, cls: 'green' },
                    ].map(s => (
                      <div key={s.name} className="stage-bar-row">
                        <span className="stage-bar-label">{s.name}</span>
                        <div className="stage-bar-track">
                          <div className={`stage-bar-fill ${s.cls}`} style={{ width: `${(s.val / s.max) * 100}%` }}></div>
                        </div>
                        <span className="stage-bar-value">{s.val}s</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="controls-card">
                  <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 600, marginBottom: 16, color: 'var(--text-primary)' }}>
                    Simulation Controls
                  </h3>
                  <div className="control-row">
                    <span className="control-label">Generator</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <button
                        onClick={() => setIsGenerating(!isGenerating)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: isGenerating ? 'var(--emerald)' : 'var(--crimson)' }}
                      >
                        {isGenerating ? <Pause size={16} /> : <Play size={16} />}
                      </button>
                      <span className="control-value">{isGenerating ? 'Active' : 'Paused'}</span>
                    </div>
                  </div>
                  <div className="control-row">
                    <span className="control-label">Velocity</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <input type="range" min="50" max="500" value={streamVelocity} onChange={(e) => setStreamVelocity(Number(e.target.value))} />
                      <span className="control-value">{streamVelocity} evt/s</span>
                    </div>
                  </div>
                  <div className="control-row">
                    <span className="control-label">Anomaly %</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <input type="range" min="0" max="50" step="0.5" value={anomalyRate} onChange={(e) => setAnomalyRate(Number(e.target.value))} />
                      <span className="control-value" style={{ color: anomalyRate > 20 ? 'var(--crimson)' : 'var(--amber)' }}>{anomalyRate}%</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Terminal */}
              <div className="terminal-panel" style={{ marginTop: 24 }}>
                <div className="terminal-header">
                  <div className="terminal-dots">
                    <div className="terminal-dot red"></div>
                    <div className="terminal-dot yellow"></div>
                    <div className="terminal-dot green"></div>
                  </div>
                  <span className="terminal-title">pipeline_telemetry.log</span>
                </div>
                <div className="terminal-body" ref={terminalRef}>
                  {logs.map(log => (
                    <div key={log.id} className={`log-line ${log.type}`}>{log.text}</div>
                  ))}
                </div>
              </div>

              {/* DB Inspector */}
              <div className="glass-card" style={{ marginTop: 24 }}>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 600, marginBottom: 16, color: 'var(--text-primary)' }}>
                  Database Inspector
                </h3>
                <div className="db-tabs">
                  {Object.keys(dbRecords).map(table => (
                    <button key={table} className={`db-tab ${dbTable === table ? 'active' : ''}`} onClick={() => setDbTable(table)}>
                      {table}
                    </button>
                  ))}
                </div>
                <table className="db-table">
                  <thead>
                    <tr>
                      {dbRecords[dbTable]?.[0] && Object.keys(dbRecords[dbTable][0]).map(col => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {dbRecords[dbTable]?.map((row, i) => (
                      <tr key={i}>
                        {Object.entries(row).map(([key, val]) => (
                          <td key={key}>
                            {(key === 'status' || key === 'state') ? (
                              <span className={`status-pill ${val.toLowerCase()}`}>{val}</span>
                            ) : val}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* ════════════════════════════════════════════════════════════════════
              TAB 4: THE CONSTELLATION (Data Flow Canvas)
          ════════════════════════════════════════════════════════════════════ */}
          {activeTab === 'constellation' && (
            <>
              <div className="section-head">
                <h2>The Constellation</h2>
                <p>Watch data particles flow through the four agents in real-time. Green sparks are valid records, red sparks are quarantined anomalies.</p>
              </div>

              <div className="constellation-canvas">
                <div className="constellation-bg"></div>

                {/* Connectors */}
                {[0, 1, 2, 3].map(i => (
                  <div
                    key={`conn-${i}`}
                    className="flow-connector"
                    style={{
                      left: `calc(${nodePositions[i].left} + 30px)`,
                      width: `calc(${parseInt(nodePositions[i + 1].left) - parseInt(nodePositions[i].left)}% - 60px)`
                    }}
                  >
                    <div className="flow-connector-line"></div>
                  </div>
                ))}

                {/* Nodes */}
                {nodePositions.map((node, i) => (
                  <div key={i} className="flow-node" style={{ left: node.left }}>
                    <div className={`flow-node-orb ${node.cls}`}>
                      {i === 0 && <Server size={22} color="white" />}
                      {i === 1 && <ArrowRight size={22} color="white" />}
                      {i === 2 && <RefreshCw size={22} color="white" />}
                      {i === 3 && <ShieldCheck size={22} color="white" />}
                      {i === 4 && <Database size={22} color="white" />}
                    </div>
                    <span className="flow-node-label">{node.label}</span>
                  </div>
                ))}

                {/* Particles */}
                {particles.map(p => {
                  const stepPercents = [10, 29, 48, 67, 86];
                  const leftPos = stepPercents[Math.min(p.step, 4)];
                  return (
                    <div
                      key={p.id}
                      className={`flow-particle ${p.isBad ? 'bad' : 'good'}`}
                      style={{ left: `${leftPos}%` }}
                    ></div>
                  );
                })}
              </div>

              {/* Live stats under canvas */}
              <div className="metrics-grid" style={{ marginTop: 0 }}>
                <div className="metric-tile green">
                  <div className="metric-tile-label"><span>Valid Records</span></div>
                  <div className="metric-tile-value" style={{ color: 'var(--emerald-glow)', fontSize: '1.4rem' }}>
                    {metrics.processedLoad.toLocaleString()}
                  </div>
                </div>
                <div className="metric-tile red">
                  <div className="metric-tile-label"><span>Quarantined</span></div>
                  <div className="metric-tile-value" style={{ color: 'var(--crimson-glow)', fontSize: '1.4rem' }}>
                    {metrics.quarantined.toLocaleString()}
                  </div>
                </div>
                <div className="metric-tile blue">
                  <div className="metric-tile-label"><span>Total Processed</span></div>
                  <div className="metric-tile-value" style={{ color: 'var(--sapphire-glow)', fontSize: '1.4rem' }}>
                    {metrics.processedIngest.toLocaleString()}
                  </div>
                </div>
                <div className="metric-tile amber">
                  <div className="metric-tile-label"><span>Kafka Lag</span></div>
                  <div className="metric-tile-value" style={{ color: 'var(--amber)', fontSize: '1.4rem' }}>
                    {kafkaLag > 0 ? kafkaLag.toLocaleString() : '0'}
                  </div>
                </div>
              </div>
            </>
          )}

          {/* ════════════════════════════════════════════════════════════════════
              TAB 5: THE WATCHTOWER (System Topology)
          ════════════════════════════════════════════════════════════════════ */}
          {activeTab === 'watchtower' && (
            <>
              <div className="section-head">
                <h2>The Watchtower</h2>
                <p>Monitor all {components.length} services. Toggle switches to simulate failures and observe cascading effects.</p>
              </div>

              <div className="two-col">
                <div className="watchtower-grid">
                  {components.map(comp => (
                    <div
                      key={comp.id}
                      className={`service-card ${selectedComp.id === comp.id ? 'selected' : ''}`}
                      onClick={() => setSelectedComp(comp)}
                    >
                      <div className="service-header">
                        <span className="service-name">{comp.name}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }} onClick={e => e.stopPropagation()}>
                          <label className="toggle-switch">
                            <input type="checkbox" checked={comp.status === 'up'} onChange={() => toggleComponentStatus(comp.id)} />
                            <span className="toggle-slider"></span>
                          </label>
                          <span className={`service-status ${comp.status}`}>{comp.status}</span>
                        </div>
                      </div>
                      <div className="service-stats">
                        <div className="service-stat">
                          <span className="service-stat-key">Port</span>
                          <span className="service-stat-val">{comp.port === '—' ? 'IPC' : comp.port}</span>
                        </div>
                        <div className="service-stat">
                          <span className="service-stat-key">Memory</span>
                          <span className="service-stat-val">{comp.memory}</span>
                        </div>
                        <div className="service-stat">
                          <span className="service-stat-key">Latency</span>
                          <span className="service-stat-val">{comp.lag}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Detail Panel */}
                <div className="detail-panel">
                  <div className="detail-panel-type">{selectedComp.type} details</div>
                  <div className="detail-panel-title">{selectedComp.name}</div>
                  <div className="detail-panel-desc">{selectedComp.description}</div>
                  <div className="detail-row">
                    <span className="detail-key">Status</span>
                    <span className="detail-val" style={{ color: selectedComp.status === 'up' ? 'var(--emerald)' : 'var(--crimson)' }}>
                      ● {selectedComp.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-key">Port</span>
                    <span className="detail-val">{selectedComp.port}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-key">Memory</span>
                    <span className="detail-val">{selectedComp.memory}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-key">Latency</span>
                    <span className="detail-val">{selectedComp.lag}</span>
                  </div>
                </div>
              </div>

              {/* Pre-Deploy Checklist */}
              <div className="glass-card" style={{ marginTop: 24 }}>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 600, marginBottom: 16, color: 'var(--text-primary)' }}>
                  Pre-Deploy Safety Checklist
                </h3>
                <div className="checklist-list">
                  {checklist.map(item => (
                    <div key={item.id} className="checklist-item" onClick={() => setChecklist(prev => prev.map(c => c.id === item.id ? { ...c, checked: !c.checked } : c))}>
                      <div className={`checklist-check ${item.checked ? 'checked' : ''}`}>
                        {item.checked && <Check size={12} color="white" />}
                      </div>
                      <span className={`checklist-text ${item.checked ? 'checked' : ''}`}>{item.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* ════════════════════════════════════════════════════════════════════
              TAB 6: THE QUARANTINE
          ════════════════════════════════════════════════════════════════════ */}
          {activeTab === 'quarantine' && (
            <>
              <div className="section-head">
                <h2>The Quarantine</h2>
                <p>Records flagged by the Quality Validation Agent. Review, edit JSON payloads, and approve or reject reprocessing.</p>
              </div>

              <div className="quarantine-grid">
                {quarantineRecords.map(rec => (
                  <div key={rec.id} className="quarantine-record">
                    <div className="qr-header">
                      <span className="qr-id">{rec.id}</span>
                      <span className="qr-time">{rec.timestamp}</span>
                    </div>
                    <div className="qr-error">
                      <AlertTriangle size={14} style={{ color: 'var(--crimson)', verticalAlign: 'middle', marginRight: 6 }} />
                      {rec.error}
                    </div>

                    {editingRecord === rec.id ? (
                      <>
                        <textarea
                          className="json-editor"
                          value={editorPayload}
                          onChange={e => {
                            setEditorPayload(e.target.value);
                            try { JSON.parse(e.target.value); setJsonParseError(null); } catch (err) { setJsonParseError(err.message); }
                          }}
                        />
                        {jsonParseError && <div className="json-error">⚠ {jsonParseError}</div>}
                        <div className="qr-actions">
                          <button className="qr-btn approve" onClick={() => {
                            if (!jsonParseError) {
                              setQuarantineRecords(prev => prev.filter(r => r.id !== rec.id));
                              setEditingRecord(null);
                              setLogs(prev => [...prev, { id: Date.now(), type: 'success', text: `[${new Date().toLocaleTimeString()}] ✦ ${rec.id} approved and requeued` }]);
                            }
                          }}>
                            <Check size={12} /> Approve
                          </button>
                          <button className="qr-btn" onClick={() => { setEditingRecord(null); setJsonParseError(null); }}>
                            Cancel
                          </button>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="qr-payload">{rec.payload}</div>
                        <div className="qr-actions">
                          <button className="qr-btn" onClick={() => { setEditingRecord(rec.id); setEditorPayload(rec.payload); setJsonParseError(null); }}>
                            <Edit3 size={12} /> Edit & Fix
                          </button>
                          <button className="qr-btn approve" onClick={() => {
                            setQuarantineRecords(prev => prev.filter(r => r.id !== rec.id));
                            setLogs(prev => [...prev, { id: Date.now(), type: 'success', text: `[${new Date().toLocaleTimeString()}] ✦ ${rec.id} approved as-is` }]);
                          }}>
                            <Check size={12} /> Approve
                          </button>
                          <button className="qr-btn reject" onClick={() => {
                            setQuarantineRecords(prev => prev.filter(r => r.id !== rec.id));
                            setLogs(prev => [...prev, { id: Date.now(), type: 'warning', text: `[${new Date().toLocaleTimeString()}] ⚑ ${rec.id} rejected and discarded` }]);
                          }}>
                            <Trash2 size={12} /> Reject
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))}
                {quarantineRecords.length === 0 && (
                  <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
                    <ShieldCheck size={40} style={{ marginBottom: 12, opacity: 0.4 }} />
                    <div style={{ fontSize: '1rem', fontWeight: 500 }}>All clear</div>
                    <div style={{ fontSize: '0.85rem', marginTop: 4 }}>No quarantined records pending review.</div>
                  </div>
                )}
              </div>
            </>
          )}

          {/* ════════════════════════════════════════════════════════════════════
              TAB 7: THE CODEX (Development Fable)
          ════════════════════════════════════════════════════════════════════ */}
          {activeTab === 'codex' && (
            <div className="codex-page">
              <div className="codex-header">
                <h2>The Codex</h2>
                <p>"A living record of every decision, discovery, and lesson from the forge."</p>
              </div>

              {CODEX_ENTRIES.map((entry, i) => (
                <div key={i} className="codex-entry">
                  <div className="codex-entry-title">{entry.title}</div>
                  <div className="codex-entry-date">{entry.date}</div>
                  <div className="codex-text">{entry.text}</div>
                  {entry.quote && <div className="codex-quote">{entry.quote}</div>}
                  {entry.milestone && (
                    <div className="codex-milestone">
                      <Award size={14} /> {entry.milestone}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

        </div>
      </main>

      {/* ──── COMMAND PALETTE (Cmd+K) ──── */}
      {cmdOpen && (
        <div className="cmd-palette-overlay" onClick={() => setCmdOpen(false)}>
          <div className="cmd-palette" onClick={e => e.stopPropagation()}>
            <div className="cmd-input-wrap">
              <Search size={16} />
              <input
                ref={cmdInputRef}
                className="cmd-input"
                placeholder="Search tabs, sessions, bugs, services..."
                value={cmdQuery}
                onChange={e => { setCmdQuery(e.target.value); setCmdActiveIdx(0); }}
                onKeyDown={e => {
                  if (e.key === 'ArrowDown') { e.preventDefault(); setCmdActiveIdx(i => Math.min(i + 1, filteredCmdItems.length - 1)); }
                  if (e.key === 'ArrowUp') { e.preventDefault(); setCmdActiveIdx(i => Math.max(i - 1, 0)); }
                  if (e.key === 'Enter' && filteredCmdItems[cmdActiveIdx]) { executeCmdItem(filteredCmdItems[cmdActiveIdx]); }
                }}
              />
            </div>
            <div className="cmd-results">
              {filteredCmdItems.length > 0 ? (
                <>
                  {['tab', 'action', 'session', 'bug', 'service'].map(type => {
                    const items = filteredCmdItems.filter(i => i.type === type);
                    if (items.length === 0) return null;
                    const labels = { tab: 'NAVIGATE', action: 'ACTIONS', session: 'SESSIONS', bug: 'BUGS', service: 'SERVICES' };
                    return (
                      <div key={type}>
                        <div className="cmd-section-label">{labels[type]}</div>
                        {items.map(item => {
                          const globalIdx = filteredCmdItems.indexOf(item);
                          const IconComp = item.icon;
                          return (
                            <div
                              key={item.id}
                              className={`cmd-result-item ${globalIdx === cmdActiveIdx ? 'active' : ''}`}
                              onClick={() => executeCmdItem(item)}
                              onMouseEnter={() => setCmdActiveIdx(globalIdx)}
                            >
                              <IconComp size={16} />
                              <span>{item.label}</span>
                              {item.shortcut && <span className="cmd-result-meta">{item.shortcut}</span>}
                              {item.meta && <span className="cmd-result-meta">{item.meta}</span>}
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </>
              ) : (
                <div className="cmd-empty">
                  <Search size={28} />
                  <div>No results for "{cmdQuery}"</div>
                </div>
              )}
            </div>
            <div className="cmd-footer">
              <div><kbd>↑</kbd><kbd>↓</kbd> navigate <kbd>↵</kbd> select</div>
              <div><kbd>esc</kbd> close</div>
            </div>
          </div>
        </div>
      )}

      {/* ──── TOAST NOTIFICATIONS ──── */}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast ${t.type}`}>
            {t.type === 'success' && <CheckCircle size={16} />}
            {t.type === 'error' && <AlertTriangle size={16} />}
            {t.type === 'warning' && <AlertTriangle size={16} />}
            {t.type === 'info' && <Info size={16} />}
            <span>{t.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
