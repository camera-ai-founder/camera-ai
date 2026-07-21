-- ==========================================================
-- DAY 33: THE SOCIAL HOLE
-- Deterministic Social Matrices & Emergent Relationships
-- ==========================================================
--
-- This table stores the active SocialDNA graph for each project.
--
-- There are two kinds of rows:
--
-- 1. MASTER ROW
--    - player_id IS NULL
--    - stores the full true SocialDNA for the project
--    - visible only to the project owner and service role
--
-- 2. PLAYER VIEW ROW
--    - player_id IS NOT NULL
--    - stores only the SocialDNA that this player has uncovered
--    - visible only to that player
--
-- This prevents players from seeing hidden reputations,
-- secret rivalries, or undiscovered faction relationships.
-- ==========================================================

create extension if not exists "pgcrypto";

-- ==========================================================
-- TABLE
-- ==========================================================

create table if not exists public.social_matrices (
    id uuid primary key default gen_random_uuid(),

    project_id uuid not null
        references public.projects(id)
        on delete cascade,

    owner_id uuid not null default auth.uid()
        references auth.users(id)
        on delete cascade,

    -- If NULL, this is the master truth row.
    -- If NOT NULL, this is a filtered player view row.
    player_id uuid
        references auth.users(id)
        on delete cascade,

    -- The social entity ID this player controls inside the Social Matrix.
    -- Usually 'player', but can be a custom NPC or avatar ID.
    player_entity_id text not null default 'player',

    -- The active SocialDNA graph.
    -- For master rows, this is the full truth.
    -- For player rows, this should be filtered to uncovered entities.
    social_dna jsonb not null default '{}'::jsonb,

    -- The social entity IDs this player has uncovered.
    -- Example:
    -- ['player', 'faction_merchants', 'faction_iron_guard', 'npc_ivan']
    discovered_entity_ids text[] not null default '{}',

    version integer not null default 1,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    constraint social_matrices_social_dna_object
        check (jsonb_typeof(social_dna) = 'object'),

    constraint social_matrices_version_positive
        check (version >= 1),

    constraint social_matrices_player_entity_id_not_empty
        check (length(btrim(player_entity_id)) > 0)
);

comment on table public.social_matrices is
    'Day 33: Deterministic Social Matrix ledger. Master rows store full SocialDNA. Player rows store uncovered SocialDNA.';

comment on column public.social_matrices.project_id is
    'The project this social matrix belongs to.';

comment on column public.social_matrices.owner_id is
    'The project owner who controls the master social truth.';

comment on column public.social_matrices.player_id is
    'NULL for master truth row. NOT NULL for a filtered player view row.';

comment on column public.social_matrices.player_entity_id is
    'The social entity ID representing this player inside the Social Matrix.';

comment on column public.social_matrices.social_dna is
    'Full SocialDNA for master rows. Filtered SocialDNA for player rows.';

comment on column public.social_matrices.discovered_entity_ids is
    'The social entity IDs this player has uncovered.';

-- ==========================================================
-- INDEXES
-- ==========================================================

create index if not exists social_matrices_project_id_idx
    on public.social_matrices (project_id);

create index if not exists social_matrices_owner_id_idx
    on public.social_matrices (owner_id);

create index if not exists social_matrices_player_id_idx
    on public.social_matrices (player_id);

create index if not exists social_matrices_discovered_entity_ids_gin_idx
    on public.social_matrices
    using gin (discovered_entity_ids);

create index if not exists social_matrices_social_dna_gin_idx
    on public.social_matrices
    using gin (social_dna);

-- Only one master truth row per project.
create unique index if not exists social_matrices_one_master_per_project_idx
    on public.social_matrices (project_id)
    where player_id is null;

-- Only one player view row per project per player.
create unique index if not exists social_matrices_one_player_view_per_project_idx
    on public.social_matrices (project_id, player_id)
    where player_id is not null;

-- ==========================================================
-- UPDATED AT TRIGGER
-- ==========================================================

create or replace function public.set_social_matrices_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists social_matrices_set_updated_at
    on public.social_matrices;

create trigger social_matrices_set_updated_at
    before update on public.social_matrices
    for each row
    execute function public.set_social_matrices_updated_at();

-- ==========================================================
-- ROW LEVEL SECURITY
-- ==========================================================

alter table public.social_matrices enable row level security;

-- Protective: even table owners should respect RLS unless explicitly bypassing.
alter table public.social_matrices force row level security;

-- ----------------------------------------------------------
-- SELECT
-- ----------------------------------------------------------
-- Owners can see all rows for matrices they own.
-- Players can see only their own player view row.
-- ----------------------------------------------------------

drop policy if exists "social_matrices_select_owner_or_player"
    on public.social_matrices;

create policy "social_matrices_select_owner_or_player"
    on public.social_matrices
    for select
    to authenticated
    using (
        owner_id = auth.uid()
        or player_id = auth.uid()
    );

-- ----------------------------------------------------------
-- INSERT
-- ----------------------------------------------------------
-- Only owners may insert master rows or player view rows.
-- Service role can bypass RLS when the backend needs to write.
-- Players cannot create social truth.
-- ----------------------------------------------------------

drop policy if exists "social_matrices_insert_owner_only"
    on public.social_matrices;

create policy "social_matrices_insert_owner_only"
    on public.social_matrices
    for insert
    to authenticated
    with check (
        owner_id = auth.uid()
    );

-- ----------------------------------------------------------
-- UPDATE
-- ----------------------------------------------------------
-- Only owners may update social matrices.
-- Players cannot modify reputations.
-- ----------------------------------------------------------

drop policy if exists "social_matrices_update_owner_only"
    on public.social_matrices;

create policy "social_matrices_update_owner_only"
    on public.social_matrices
    for update
    to authenticated
    using (
        owner_id = auth.uid()
    )
    with check (
        owner_id = auth.uid()
    );

-- ----------------------------------------------------------
-- DELETE
-- ----------------------------------------------------------
-- Only owners may delete social matrices.
-- ----------------------------------------------------------

drop policy if exists "social_matrices_delete_owner_only"
    on public.social_matrices;

create policy "social_matrices_delete_owner_only"
    on public.social_matrices
    for delete
    to authenticated
    using (
        owner_id = auth.uid()
    );

-- ==========================================================
-- HELPER FUNCTION: FILTER SOCIAL DNA
-- ==========================================================
-- This filters a master SocialDNA graph down to only the
-- entities a player has uncovered.
--
-- A relationship is visible only if BOTH source and target
-- have been discovered.
-- ==========================================================

create or replace function public.filter_social_dna_for_entities(
    p_social_dna jsonb,
    p_entity_ids text[]
)
returns jsonb
language sql
stable
set search_path = public
as $$
    select coalesce(p_social_dna, '{}'::jsonb) || jsonb_build_object(
        'factions',
        coalesce(
            (
                select jsonb_agg(f.elem)
                from jsonb_array_elements(
                    coalesce(p_social_dna -> 'factions', '[]'::jsonb)
                ) as f(elem)
                where f.elem ->> 'faction_id' = any(coalesce(p_entity_ids, '{}'))
            ),
            '[]'::jsonb
        ),

        'relationship_tensors',
        coalesce(
            (
                select jsonb_agg(r.elem)
                from jsonb_array_elements(
                    coalesce(p_social_dna -> 'relationship_tensors', '[]'::jsonb)
                ) as r(elem)
                where r.elem ->> 'source_id' = any(coalesce(p_entity_ids, '{}'))
                  and r.elem ->> 'target_id' = any(coalesce(p_entity_ids, '{}'))
            ),
            '[]'::jsonb
        ),

        'social_rules',
        coalesce(
            (
                select jsonb_agg(s.elem)
                from jsonb_array_elements(
                    coalesce(p_social_dna -> 'social_rules', '[]'::jsonb)
                ) as s(elem)
                where (
                    s.elem ->> 'source_faction_id' is null
                    or s.elem ->> 'source_faction_id' = any(coalesce(p_entity_ids, '{}'))
                )
                and (
                    s.elem ->> 'target_faction_id' is null
                    or s.elem ->> 'target_faction_id' = any(coalesce(p_entity_ids, '{}'))
                )
            ),
            '[]'::jsonb
        ),

        'metadata',
        coalesce(p_social_dna -> 'metadata', '{}'::jsonb) || jsonb_build_object(
            'filtered_for_entities', to_jsonb(coalesce(p_entity_ids, '{}')),
            'filtered_at', to_jsonb(now())
        )
    );
$$;

comment on function public.filter_social_dna_for_entities(jsonb, text[]) is
    'Filters SocialDNA so players only see factions, relationships, and rules they have uncovered.';

-- ==========================================================
-- HELPER FUNCTION: SYNC PLAYER VIEW
-- ==========================================================
-- This creates or updates a filtered player view row from
-- the master SocialDNA row.
--
-- Only the project owner may run this.
-- Service role can also write directly if needed.
-- ==========================================================

create or replace function public.sync_social_player_view(
    p_project_id uuid,
    p_player_id uuid,
    p_discovered_entity_ids text[]
)
returns void
language plpgsql
security invoker
set search_path = public
as $$
declare
    v_master record;
    v_filtered jsonb;
    v_entities text[];
begin
    if p_project_id is null then
        raise exception 'p_project_id is required.';
    end if;

    if p_player_id is null then
        raise exception 'p_player_id is required.';
    end if;

    v_entities := coalesce(p_discovered_entity_ids, '{}');

    select *
    into v_master
    from public.social_matrices
    where project_id = p_project_id
      and player_id is null
    limit 1;

    if not found then
        raise exception 'Master social matrix not found for project %.', p_project_id;
    end if;

    if v_master.owner_id <> auth.uid() then
        raise exception 'Only the project owner can sync social player views.';
    end if;

    v_filtered := public.filter_social_dna_for_entities(
        v_master.social_dna,
        v_entities
    );

    insert into public.social_matrices (
        project_id,
        owner_id,
        player_id,
        player_entity_id,
        social_dna,
        discovered_entity_ids,
        version
    )
    values (
        p_project_id,
        v_master.owner_id,
        p_player_id,
        coalesce(v_master.player_entity_id, 'player'),
        v_filtered,
        v_entities,
        1
    )
    on conflict (project_id, player_id)
    where player_id is not null
    do update set
        social_dna = excluded.social_dna,
        discovered_entity_ids = excluded.discovered_entity_ids,
        player_entity_id = excluded.player_entity_id,
        version = public.social_matrices.version + 1;
end;
$$;

comment on function public.sync_social_player_view(uuid, uuid, text[]) is
    'Creates or updates a filtered SocialDNA player view row from the master SocialDNA row.';
