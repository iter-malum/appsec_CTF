export type User = {
  id: number;
  username: string;
  display_name: string;
  role: "participant" | "admin";
  team_id: number | null;
  is_active: boolean;
  created_at: string;
};

export type RubricItem = {
  id: string;
  title: string;
  max_points: number;
  description?: string;
};

export type RubricScoreItem = RubricItem & { score: number };

export type EventContent = {
  title: string;
  description_md: string;
  challenge_md: string;
  has_source: boolean;
  source_filename: string | null;
  rubric: RubricItem[];
  updated_at: string | null;
};

export type TeamMember = {
  id: number;
  username: string;
  display_name: string;
  is_owner: boolean;
};

export type TeamInvite = {
  id: number;
  team_id: number;
  team_name: string;
  inviter_username: string;
  invitee_username: string;
  status: string;
  created_at: string;
};

export type Team = {
  id: number;
  name: string;
  owner_id: number;
  members: TeamMember[];
  pending_invites: TeamInvite[];
  created_at: string;
};

export type Report = {
  id: number;
  team_id: number;
  team_name: string;
  original_filename: string;
  note: string | null;
  submitted_by: string;
  submitted_at: string;
  updated_at: string;
  judge_id: number | null;
  judge_username: string | null;
  rubric_scores: RubricScoreItem[];
  total_score: number | null;
  comment: string | null;
  is_published: boolean;
  scored_at: string | null;
  published_at: string | null;
  can_view_score: boolean;
};

export type Message = {
  id: number;
  author_id: number;
  author_username: string;
  author_role: string;
  body: string;
  created_at: string;
};

export type Ticket = {
  id: number;
  team_id: number;
  team_name: string;
  status: string;
  messages: Message[];
  updated_at: string;
};

export type NotificationItem = {
  id: number;
  title: string;
  body: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
};
