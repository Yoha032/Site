-- Таблица лидеров для игры. Выполни в Supabase: SQL Editor → New query → Run.

create table if not exists public.scores (
  id         bigint generated always as identity primary key,
  name       text not null check (char_length(name) between 1 and 12),
  score      int  not null check (score between 1 and 99999),
  created_at timestamptz not null default now()
);

alter table public.scores enable row level security;

-- Все могут читать таблицу
create policy "scores are readable by everyone"
  on public.scores for select
  using (true);

-- Все могут добавлять результат, но не менять и не удалять чужие
create policy "anyone can add a score"
  on public.scores for insert
  with check (char_length(name) between 1 and 12 and score between 1 and 99999);

-- Быстрая сортировка для топа
create index if not exists scores_top_idx on public.scores (score desc, created_at asc);
