export type AdminProfile = {
  id: number;
  email: string;
  role: "ADMIN" | "SYS_ADMIN";
  is_active: boolean;
};

export type AuditLog = {
  id: number;
  created_at: string;
  actor_type: string;
  actor_user_id?: number | null;
  actor_tg_user_id?: number | null;
  actor_role?: string | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  meta: Record<string, unknown>;
  ip?: string | null;
  user_agent?: string | null;
};

export type ServiceCategory = {
  id: number;
  title: string;
  slug: string;
  sort_order: number;
  is_active: boolean;
};

export type Service = {
  id: number;
  category_id: number;
  category?: ServiceCategory;
  title: string;
  slug: string;
  short_description: string;
  description: string;
  duration_min: number;
  price_from: number;
  price_to?: number | null;
  discount_percent?: number | null;
  image_url?: string | null;
  tags: string[];
  is_active: boolean;
  sort_order: number;
  seo_title?: string | null;
  seo_description?: string | null;
};


export type Master = {
  id: number;
  name: string;
  slug: string;
  photo_url?: string | null;
  short_bio?: string | null;
  bio?: string | null;
  is_active: boolean;
  sort_order: number;
  telegram_user_id?: number | null;
  telegram_chat_id?: number | null;
  telegram_username?: string | null;
  telegram_link_code?: string | null;
  telegram_linked_at?: string | null;
  services?: Service[];
};

export type WeeklyRitual = {
  id: number;
  title: string;
  slug?: string | null;
  short_description?: string | null;
  description: string;
  image_url?: string | null;
  cta_text?: string | null;
  cta_url?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_active: boolean;
  sort_order: number;
};

export type Review = {
  id: number;
  author_name: string;
  rating?: number | null;
  text: string;
  source?: string | null;
  source_url?: string | null;
  review_date?: string | null;
  is_published: boolean;
  sort_order: number;
};

export type AvailabilitySlot = {
  starts_at: string;
  ends_at: string;
};

export type Booking = {
  id: number;
  client_name: string;
  client_phone: string;
  service_id: number;
  starts_at: string;
  ends_at: string;
  comment?: string | null;
  status: string;
  source: string;
  is_read: boolean;
  admin_comment?: string | null;
  final_price_cents?: number | null;
  created_at: string;
  service?: Service;
  master?: Master | null;
};

export type SettingsPayload = Record<string, unknown>;


export type BookingSlot = {
  time: string;
  starts_at: string;
  ends_at: string;
};


export type ScheduleMaster = {
  id: number;
  name: string;
};

export type ScheduleBooking = {
  id: number;
  master_id?: number | null;
  service_id: number;
  service_title?: string | null;
  starts_at: string;
  ends_at: string;
  status: string;
  client_name: string;
  client_phone: string;
  source: "public" | "admin" | string;
};

export type AdminScheduleResponse = {
  mode: "day" | "week";
  date_from: string;
  date_to: string;
  slot_step_min: number;
  masters: ScheduleMaster[];
  bookings: ScheduleBooking[];
};

export type AdminAvailabilityResponse = {
  date: string;
  slot_step_min: number;
  service: {
    id: number;
    duration_min: number;
    title: string;
  };
  masters: ScheduleMaster[];
  slots_by_master: Record<string, string[]>;
};
