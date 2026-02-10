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
  created_at: string;
};

export type SettingsPayload = Record<string, unknown>;


export type BookingSlot = {
  time: string;
  starts_at: string;
  ends_at: string;
};
