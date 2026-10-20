export type Fact = {
  id: string;
  task_id: string;
  field: string;
  value: string | number | null;
  quote: string;
  page: number;
  source_id: string;
  source_version: string;
  hash: string;
  fetched_at: string;
  timezone: string;
  status: string;
  kind: string;
};
export type Source = {
  import_notice?: string;
  id: string;
  title: string;
  filename: string;
  version: string;
  content_hash: string;
  fetched_at: string;
  mode: string;
  facts: Fact[];
  pages?: { page: number; text: string }[];
  remote?: { url: string; commit: string };
};
export type Task = {
  remaining_minutes?: number | null;
  progress?: { remaining_minutes: number | null; completion: string };
  id: string;
  title: string;
  course: string;
  minutes: number | null;
  effort_max: number | null;
  due: string | null;
  source_ids: string[];
  rubric: string[];
  completion: string;
  gaps: string[];
  user_overrides?: Record<string, unknown>;
  section_key: string;
  identity: {
    status: string;
    course: string;
    term: string | null;
    assignment_key: string;
    origin: string;
  };
};
export type Block = {
  task_id: string;
  start: string;
  end: string;
  pinned: boolean;
};
export type Plan = {
  scope?: {
    included: string[];
    excluded: { id: string; title: string; gaps: string[] }[];
    complete: boolean;
  };
  id: string;
  blocks: Block[];
  feasible: boolean;
  solver_status: string;
  capacity_minutes: number;
  required_minutes: number;
  scheduled_minutes: number;
  unscheduled_minutes: number;
  unscheduled_by_task: Record<string, number>;
  slack_minutes: number;
  created_at: string;
  invalidated?: boolean;
  assumptions: string[];
  preserved_units: number;
  input: {
    tasks: Task[];
    windows: { start: string; end: string }[];
    timezone: string;
  };
};
export type RunEvent = {
  sequence: number;
  run_id: string;
  type: string;
  timestamp: string;
  tool?: string;
  summary?: string;
  duration_ms?: number;
  mode?: string;
  code?: string;
};
export type Conflict = {
  id: string;
  task_id: string;
  facts: Fact[];
  status: string;
  resolution?: { fact_id: string; policy: string };
};
export type Receipt = {
  id: string;
  plan_id: string;
  calendar_id: string;
  status: string;
  mode: string;
  created_at: string;
  outcomes: {
    event_id: string;
    status: string;
    url?: string;
    verified_at?: string;
    etag?: string;
    error?: { message: string; code?: string };
  }[];
};
export type Snapshot = {
  calendar_error?: { code: string; message: string } | null;
  workspace_fingerprint?: string;
  additions_revision?: number;
  workspace_id?: string;
  calendar_events?: {
    id: string;
    summary: string;
    etag?: string;
    extendedProperties?: { private?: { relay_task?: string } };
    start: { dateTime?: string; date?: string };
    end: { dateTime?: string; date?: string };
  }[];
  calendar_mode?: string;
  settings: {
    ai_access?: boolean;
    portable_origin?: string;
    mode: string;
    timezone: string;
    anchor: string;
    range_end?: string;
    calendar_id: string;
    calendar_live: boolean;
    github_repo: string;
    watch_enabled: boolean;
    poll_seconds?: number;
    windows: { start: string; end: string }[];
  };
  tasks: Task[];
  sources: Source[];
  conflicts: Conflict[];
  plan: Plan | null;
  events: RunEvent[];
  receipts: Receipt[];
  last_sync: string | null;
  snapshot_generated_at: string;
  freshness: {
    last_successful_sync: string | null;
    source_fetched_at: string | null;
    last_failed_attempt: { at: string; code: string } | null;
  };
  agent: {
    configured: boolean;
    resource: string | null;
    verified: boolean;
    provider?: string;
    deployment_mode?: string;
    model?: string;
    managed_agent_engine?: boolean;
    public_access?: boolean;
  };
  demo?: {
    public: boolean;
    storage: string;
    session_seconds: number;
    max_upload_mib: number;
    max_sources: number;
  };
};
export type Preview = {
  id: string;
  plan_id: string;
  calendar_id: string;
  mode: string;
  digest: string;
  expires_at: string;
  actions: {
    operation: string;
    event: {
      id: string;
      summary: string;
      start: { dateTime: string };
      end: { dateTime: string };
    };
  }[];
};
export type Packet = {
  task: Task;
  objective: string | null;
  next_action: string;
  checklist: string[];
  facts: Fact[];
  duration_assumption: string;
  completion_origin: string;
  graph: {
    from_id: string;
    to_id: string;
    relation: string;
    fact_id: string;
  }[];
};
declare global {
  interface Window {
    relay?: {
      request: (
        path: string,
        method?: string,
        body?: unknown,
      ) => Promise<unknown>;
      connectGoogle: () => Promise<void>;
      importFile: (
        kind?: "passport",
      ) => Promise<{ name: string; content: string } | null>;
      notify: (title: string, body: string) => Promise<void>;
      openExternal: (url: string) => Promise<void>;
      saveSnapshot: (data: unknown) => Promise<void>;
      savePassport: (data: unknown) => Promise<{ saved: boolean }>;
      loadSnapshot: (tenant?: string | null) => Promise<Snapshot | null>;
      version: () => Promise<string>;
      setLanguage: (language: "en" | "ru" | "kk") => Promise<void>;
      watchFolder: () => Promise<{ enabled: boolean; path?: string }>;
      onFiles: (
        cb: (files: { name: string; content: string }[]) => void,
      ) => () => void;
    };
  }
}
