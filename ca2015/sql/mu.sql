begin;

drop table if exists fifa.men_mu;

create table fifa.men_mu (
       team_id	       text,
       team_name       text,
       opponent_id     text,
       opponent_name   text,
       team_mu	       float,
       opponent_mu     float,
       primary key (team_id,opponent_id)
);

insert into fifa.men_mu
(team_id,team_name,opponent_id,opponent_name,team_mu,opponent_mu)
(
select
s1.team_id,t1.team_name,
s2.team_id,t2.team_name,

exp(bf.estimate)*h.offensive*v.defensive,
exp(bf.estimate)*v.offensive*h.defensive

from fifa.men_schedule_factors s1
join fifa.men_schedule_factors s2
  on (s1.team_id<>s2.team_id)
join fifa.teams t1
  on (t1.team_id,t1.gender_id)=(s1.team_id,'men')
join fifa.teams t2
  on (t2.team_id,t2.gender_id)=(s2.team_id,'men')
join fifa.men_schedule_factors h
  on (h.team_id)=(t1.team_id)
join fifa.men_schedule_factors v
  on (v.team_id)=(t2.team_id)
join fifa.men_basic_factors bf
  on bf.factor='(Intercept)'

where

    s1.team_id in
    ('per', 'arg', 'par')
and s2.team_id in
    ('per', 'arg', 'par')
);

insert into fifa.men_mu
(team_id,team_name,opponent_id,opponent_name,team_mu,opponent_mu)
(
select
s1.team_id,t1.team_name,
s2.team_id,t2.team_name,

exp(bf.estimate)*h.offensive*v.defensive*o.exp_factor,
exp(bf.estimate)*v.offensive*h.defensive*d.exp_factor

from fifa.men_schedule_factors s1
join fifa.men_schedule_factors s2
  on (s1.team_id<>s2.team_id)
join fifa.teams t1
  on (t1.team_id,t1.gender_id)=(s1.team_id,'men')
join fifa.teams t2
  on (t2.team_id,t2.gender_id)=(s2.team_id,'men')
join fifa.men_schedule_factors h
  on (h.team_id)=(t1.team_id)
join fifa.men_schedule_factors v
  on (v.team_id)=(t2.team_id)
join fifa.men_factors o
  on (o.parameter,o.level)=('field','offense_home')
join fifa.men_factors d
  on (d.parameter,d.level)=('field','defense_home')
join fifa.men_basic_factors bf
  on bf.factor='(Intercept)'

where

    s1.team_id in
    ('chi')
and s2.team_id in
    ('per', 'arg', 'par')
);

insert into fifa.men_mu
(team_id,team_name,opponent_id,opponent_name,team_mu,opponent_mu)
(
select
s1.team_id,t1.team_name,
s2.team_id,t2.team_name,

exp(bf.estimate)*h.offensive*v.defensive*d.exp_factor,
exp(bf.estimate)*v.offensive*h.defensive*o.exp_factor

from fifa.men_schedule_factors s1
join fifa.men_schedule_factors s2
  on (s1.team_id<>s2.team_id)
join fifa.teams t1
  on (t1.team_id,t1.gender_id)=(s1.team_id,'men')
join fifa.teams t2
  on (t2.team_id,t2.gender_id)=(s2.team_id,'men')
join fifa.men_schedule_factors h
  on (h.team_id)=(t1.team_id)
join fifa.men_schedule_factors v
  on (v.team_id)=(t2.team_id)
join fifa.men_factors o
  on (o.parameter,o.level)=('field','offense_home')
join fifa.men_factors d
  on (d.parameter,d.level)=('field','defense_home')
join fifa.men_basic_factors bf
  on bf.factor='(Intercept)'

where

    s1.team_id in
    ('per', 'arg', 'par')
and s2.team_id in
    ('chi')
);

commit;
