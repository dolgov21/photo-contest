import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


async def get_contest_games_info(app: "Application", contest_id: int) -> str:
    contest = await app.store.db.get_contest_with_details(contest_id)
    if not contest:
        return "Информация о играх недоступна."

    info_parts = ["📊 <b>Статистика конкурса:</b>"]

    participants = contest.participants
    info_parts.append(f"👥 Участников: {len(participants)}")

    if contest.rounds:
        info_parts.append(f"🎯 Текущий раунд: {contest.current_round or 0}")

        total_matches = 0
        finished_matches = 0
        active_matches = 0

        for round_obj in contest.rounds:
            total_matches += len(round_obj.matches)
            finished_matches += sum(
                1 for match in round_obj.matches if match.is_finished
            )
            active_matches += sum(
                1 for match in round_obj.matches if not match.is_finished
            )

        info_parts.append(f"⚔️ Создано матчей: {total_matches}")

        if finished_matches > 0:
            info_parts.append(f"✅ Завершено: {finished_matches}")
        if active_matches > 0:
            info_parts.append(f"🔄 Активных: {active_matches}")
    else:
        info_parts.append("📝 Раунды еще не созданы")

    return "\n".join(info_parts)