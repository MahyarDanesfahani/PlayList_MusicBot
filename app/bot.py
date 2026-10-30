"""Telegram bot creation and update handlers."""

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func
from sqlalchemy import delete, select

from app.config import get_bot_token
from app.database.session import get_session
from app.keyboards.language import language_keyboard
from app.keyboards.playlist import main_menu, playlist_actions, song_actions
from app.keyboards.recommendation import recommendation_keyboard
from app.models.playlist import Playlist
from app.models.song import Song
from app.models.user import User


router = Router()
user_languages: dict[int, str] = {}


class PlaylistCreation(StatesGroup):
    """States used while creating a playlist."""

    waiting_for_name = State()


class SongAddition(StatesGroup):
    """State used while waiting for an audio file."""

    waiting_for_audio = State()


class SongSearch(StatesGroup):
    """State used while waiting for a song or performer search query."""

    waiting_for_query = State()


class SongRecommendation(StatesGroup):
    """States used by the mood-based recommendation questionnaire."""

    answering = State()


MESSAGES = {
    "fa": {
        "choose": "زبان خود را انتخاب کنید:",
        "welcome": (
            "سلام {name} 👋\n\n"
            "به بات پلی‌لیست موزیک خوش اومدی!\n"
            "به‌زودی می‌تونی پلی‌لیست‌های شخصی خودت رو بسازی و آهنگ‌هات رو مدیریت کنی."
        ),
            "menu": "از منوی زیر یک گزینه را انتخاب کن:",
            "ask_name": "نام پلی‌لیست جدید را ارسال کن:",
            "empty": "هنوز پلی‌لیستی نساختی.",
            "list": "پلی‌لیست‌های تو:",
            "created": "پلی‌لیست «{name}» ساخته شد.",
            "deleted": "پلی‌لیست حذف شد.",
            "ask_audio": "فایل صوتی آهنگ را ارسال کن:",
            "audio_only": "لطفاً یک فایل صوتی ارسال کن.",
            "song_added": "آهنگ به پلی‌لیست اضافه شد.",
            "songs": "آهنگ‌های پلی‌لیست:",
            "no_songs": "این پلی‌لیست هنوز آهنگی ندارد.",
            "song_deleted": "آهنگ حذف شد.",
            "ask_search": "نام آهنگ یا خواننده را برای جست‌وجو ارسال کن:",
            "search_empty": "آهنگی با این عبارت پیدا نشد.",
            "search_results": "نتایج جست‌وجو:",
            "recommend_q1": "الان بیشتر دنبال چه حسی هستی؟",
            "recommend_q2": "امروز انرژی‌ات چطور است؟",
            "recommend_q3": "کدام فضا را بیشتر می‌پسندی؟",
            "recommend_empty": "برای پیشنهاد دادن هنوز آهنگی در پلی‌لیست‌هایت نداری.",
            "recommend_found": "فکر می‌کنم این آهنگ با حال‌وهوایت جور باشد:",
            "recommend_no_match": "آهنگ کاملاً متناسب پیدا نشد، اما این گزینه را پیشنهاد می‌کنم:",
    },
    "en": {
        "choose": "Please choose your language:",
        "welcome": (
            "Hello {name} 👋\n\n"
            "Welcome to the Music Playlist Bot!\n"
            "Soon you will be able to create personal playlists and manage your songs."
        ),
            "menu": "Choose an option from the menu:",
            "ask_name": "Send the name of your new playlist:",
            "empty": "You have not created any playlists yet.",
            "list": "Your playlists:",
            "created": "Playlist “{name}” was created.",
            "deleted": "Playlist deleted.",
            "ask_audio": "Send the audio file you want to add:",
            "audio_only": "Please send an audio file.",
            "song_added": "The song was added to the playlist.",
            "songs": "Playlist songs:",
            "no_songs": "This playlist has no songs yet.",
            "song_deleted": "Song deleted.",
            "ask_search": "Send a song title or performer name to search:",
            "search_empty": "No songs matched your search.",
            "search_results": "Search results:",
            "recommend_q1": "What kind of feeling are you looking for?",
            "recommend_q2": "How is your energy level today?",
            "recommend_q3": "Which atmosphere do you prefer?",
            "recommend_empty": "You do not have any songs in your playlists yet.",
            "recommend_found": "I think this song matches your mood:",
            "recommend_no_match": "I could not find an exact mood match, but try this song:",
    },
}


RECOMMENDATION_QUESTIONS = {
    "fa": [
        ("recommend_q1", [("🌿 آرامش", "calm"), ("😊 شادی", "happy"), ("💔 تخلیه احساسات", "sad"), ("⚡ هیجان", "energetic")]),
        ("recommend_q2", [("🔋 زیاد", "energetic"), ("☕ متوسط", "calm"), ("🛋 کم", "sad")]),
        ("recommend_q3", [("🌙 خلوت و شبانه", "calm"), ("🎉 مهمانی", "happy"), ("🏃 انگیزشی", "energetic"), ("💭 نوستالژیک", "sad")]),
    ],
    "en": [
        ("recommend_q1", [("🌿 Calm", "calm"), ("😊 Happy", "happy"), ("💔 Emotional", "sad"), ("⚡ Energetic", "energetic")]),
        ("recommend_q2", [("🔋 High", "energetic"), ("☕ Medium", "calm"), ("🛋 Low", "sad")]),
        ("recommend_q3", [("🌙 Quiet and late-night", "calm"), ("🎉 Party", "happy"), ("🏃 Motivational", "energetic"), ("💭 Nostalgic", "sad")]),
    ],
}


MOOD_KEYWORDS = {
    "calm": ("آرام", "relax", "calm", "chill", "sleep", "lofi", "ambient", "acoustic"),
    "happy": ("شاد", "happy", "joy", "dance", "party", "fun", "خنده", "شادی"),
    "sad": ("غم", "sad", "heart", "broken", "emotional", "آهنگ غمگین", "دلتنگ"),
    "energetic": ("energy", "rock", "جشن", "انرژی", "gym", "motiv", "power", "dance"),
}


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Handle the /start command."""
    if message.from_user:
        async with get_session() as session:
            user = await session.scalar(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            if user is None:
                session.add(
                    User(
                        telegram_id=message.from_user.id,
                        username=message.from_user.username,
                        first_name=message.from_user.first_name,
                    )
                )
                await session.commit()

    await message.answer(
        "زبان خود را انتخاب کنید / Please choose your language:",
        reply_markup=language_keyboard(),
    )


@router.message(Command("playlists"))
async def playlists_command(message: Message) -> None:
    """Provide quick access to the user's playlists."""
    if not message.from_user:
        return
    language = await get_user_language(message.from_user.id)
    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        has_playlists = False
        if user:
            has_playlists = (
                await session.scalar(
                    select(Playlist.id).where(Playlist.user_id == user.id).limit(1)
                )
            ) is not None
    if has_playlists:
        await message.answer(MESSAGES[language]["list"], reply_markup=main_menu(language))
        await list_user_playlists(message, language)
    else:
        await message.answer(MESSAGES[language]["empty"], reply_markup=main_menu(language))


async def list_user_playlists(message: Message, language: str) -> None:
    """Send the user's playlists with their action buttons."""
    if not message.from_user:
        return
    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        if not user:
            return
        result = await session.scalars(
            select(Playlist).where(Playlist.user_id == user.id).order_by(Playlist.id)
        )
        for playlist in result:
            await message.answer(
                f"🎵 {playlist.name}",
                reply_markup=playlist_actions(playlist.id, language),
            )


@router.callback_query(lambda callback: callback.data in {"language:fa", "language:en"})
async def language_handler(callback: CallbackQuery) -> None:
    """Save the selected language for the current process and show a welcome message."""
    if not callback.from_user or not callback.message or not callback.data:
        return

    language = callback.data.split(":", maxsplit=1)[1]
    user_languages[callback.from_user.id] = language
    first_name = callback.from_user.first_name or ("دوست" if language == "fa" else "friend")

    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        if user is not None:
            user.language = language
            user.username = callback.from_user.username
            user.first_name = callback.from_user.first_name
            await session.commit()

    await callback.message.edit_text(
        MESSAGES[language]["welcome"].format(name=first_name)
    )
    await callback.message.answer(
        MESSAGES[language]["menu"], reply_markup=main_menu(language)
    )
    await callback.answer()


async def get_user_language(telegram_id: int) -> str:
    """Get a user's saved language, falling back to Persian."""
    async with get_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        return user.language if user and user.language in MESSAGES else "fa"


@router.callback_query(lambda callback: callback.data == "playlist:create")
async def create_playlist_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Ask the user for a new playlist name."""
    if not callback.from_user or not callback.message:
        return
    language = await get_user_language(callback.from_user.id)
    await state.set_state(PlaylistCreation.waiting_for_name)
    await callback.message.answer(MESSAGES[language]["ask_name"])
    await callback.answer()


async def send_recommendation_question(
    message: Message, language: str, question_index: int
) -> None:
    """Send one questionnaire question to the user."""
    message_key, options = RECOMMENDATION_QUESTIONS[language][question_index]
    await message.answer(
        MESSAGES[language][message_key],
        reply_markup=recommendation_keyboard(options),
    )


@router.callback_query(lambda callback: callback.data == "recommend:start")
async def recommendation_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Start the mood questionnaire."""
    if not callback.from_user or not callback.message:
        return
    language = await get_user_language(callback.from_user.id)
    await state.set_data({"recommendation_index": 0, "moods": []})
    await state.set_state(SongRecommendation.answering)
    await send_recommendation_question(callback.message, language, 0)
    await callback.answer()


@router.callback_query(
    SongRecommendation.answering,
    lambda callback: callback.data and callback.data.startswith("recommend:answer:"),
)
async def recommendation_answer(callback: CallbackQuery, state: FSMContext) -> None:
    """Store an answer and either ask the next question or send a recommendation."""
    if not callback.from_user or not callback.message or not callback.data:
        return

    language = await get_user_language(callback.from_user.id)
    mood = callback.data.rsplit(":", maxsplit=1)[1]
    data = await state.get_data()
    moods = list(data.get("moods", []))
    moods.append(mood)
    question_index = int(data.get("recommendation_index", 0)) + 1

    if question_index < len(RECOMMENDATION_QUESTIONS[language]):
        await state.update_data(recommendation_index=question_index, moods=moods)
        await send_recommendation_question(callback.message, language, question_index)
        await callback.answer()
        return

    await state.clear()
    await send_recommended_song(callback.message, callback.from_user.id, language, moods)
    await callback.answer()


async def send_recommended_song(
    message: Message, telegram_id: int, language: str, moods: list[str]
) -> None:
    """Choose and send the best matching song from the user's playlists."""
    mood_scores = {mood: moods.count(mood) for mood in set(moods)}
    preferred_mood = max(mood_scores, key=mood_scores.get)
    keywords = MOOD_KEYWORDS[preferred_mood]

    async with get_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user is None:
            await message.answer(MESSAGES[language]["recommend_empty"], reply_markup=main_menu(language))
            return

        songs_result = await session.scalars(
            select(Song)
            .join(Playlist, Song.playlist_id == Playlist.id)
            .where(Playlist.user_id == user.id)
            .order_by(func.random())
        )
        songs = list(songs_result)

    if not songs:
        await message.answer(MESSAGES[language]["recommend_empty"], reply_markup=main_menu(language))
        return

    matching_songs = [
        song
        for song in songs
        if any(
            keyword.casefold() in f"{song.title or ''} {song.performer or ''}".casefold()
            for keyword in keywords
        )
    ]
    song = matching_songs[0] if matching_songs else songs[0]
    message_key = "recommend_found" if matching_songs else "recommend_no_match"
    label = song.title or song.performer or "Untitled song"
    if song.performer and song.title:
        label = f"{song.title} — {song.performer}"
    await message.answer(MESSAGES[language][message_key])
    await message.answer_audio(
        audio=song.file_id,
        title=song.title,
        performer=song.performer,
        duration=song.duration,
        caption=f"🎵 {label}",
    )
    await message.answer(MESSAGES[language]["menu"], reply_markup=main_menu(language))


@router.callback_query(lambda callback: callback.data == "song:search")
async def search_song_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Ask the user for a song title or performer name."""
    if not callback.from_user or not callback.message:
        return
    language = await get_user_language(callback.from_user.id)
    await state.set_state(SongSearch.waiting_for_query)
    await callback.message.answer(MESSAGES[language]["ask_search"])
    await callback.answer()


@router.message(Command("search"))
async def search_command(message: Message, state: FSMContext) -> None:
    """Start a song search from the command line."""
    if not message.from_user:
        return
    language = await get_user_language(message.from_user.id)
    await state.set_state(SongSearch.waiting_for_query)
    await message.answer(MESSAGES[language]["ask_search"])


@router.message(SongSearch.waiting_for_query)
async def search_songs(message: Message, state: FSMContext) -> None:
    """Search the user's songs by title or performer."""
    if not message.from_user or not message.text:
        return

    query = message.text.strip()
    language = await get_user_language(message.from_user.id)
    if not query:
        await message.answer(MESSAGES[language]["ask_search"])
        return

    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        songs = []
        if user:
            result = await session.scalars(
                select(Song)
                .join(Playlist, Song.playlist_id == Playlist.id)
                .where(
                    Playlist.user_id == user.id,
                    (Song.title.ilike(f"%{query}%"))
                    | (Song.performer.ilike(f"%{query}%")),
                )
                .order_by(Song.id)
            )
            songs = list(result)

    await state.clear()
    if not songs:
        await message.answer(MESSAGES[language]["search_empty"], reply_markup=main_menu(language))
        return

    await message.answer(MESSAGES[language]["search_results"])
    for song in songs:
        label = song.title or song.performer or "Untitled song"
        if song.performer and song.title:
            label = f"{song.title} — {song.performer}"
        await message.answer(
            f"🎵 {label}", reply_markup=song_actions(song.id, language)
        )


@router.message(PlaylistCreation.waiting_for_name)
async def create_playlist(message: Message, state: FSMContext) -> None:
    """Create a playlist from the user's text message."""
    if not message.from_user or not message.text:
        return
    name = message.text.strip()
    language = await get_user_language(message.from_user.id)

    if not name or len(name) > 100:
        await message.answer(
            "نام باید بین ۱ تا ۱۰۰ کاراکتر باشد."
            if language == "fa"
            else "The name must be between 1 and 100 characters."
        )
        return

    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        if user is None:
            return
        session.add(Playlist(user_id=user.id, name=name))
        await session.commit()

    await state.clear()
    await message.answer(MESSAGES[language]["created"].format(name=name), reply_markup=main_menu(language))


@router.callback_query(lambda callback: callback.data == "playlist:list")
async def list_playlists(callback: CallbackQuery) -> None:
    """Show the current user's playlists."""
    if not callback.from_user or not callback.message:
        return
    language = await get_user_language(callback.from_user.id)
    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        playlists = []
        if user:
            result = await session.scalars(
                select(Playlist).where(Playlist.user_id == user.id).order_by(Playlist.id)
            )
            playlists = list(result)

    if not playlists:
        await callback.message.answer(MESSAGES[language]["empty"], reply_markup=main_menu(language))
    else:
        await callback.message.answer(MESSAGES[language]["list"])
        for playlist in playlists:
            await callback.message.answer(
                f"🎵 {playlist.name}",
                reply_markup=playlist_actions(playlist.id, language),
            )
    await callback.answer()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("playlist:delete:"))
async def delete_playlist(callback: CallbackQuery) -> None:
    """Delete a playlist only if it belongs to the current user."""
    if not callback.from_user or not callback.message or not callback.data:
        return
    playlist_id = int(callback.data.rsplit(":", maxsplit=1)[1])
    language = await get_user_language(callback.from_user.id)
    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        if user:
            await session.execute(
                delete(Playlist).where(
                    Playlist.id == playlist_id, Playlist.user_id == user.id
                )
            )
            await session.commit()
    await callback.message.edit_text(MESSAGES[language]["deleted"])
    await callback.answer()


async def owned_playlist(session, telegram_id: int, playlist_id: int) -> Playlist | None:
    """Return a playlist only when it belongs to the Telegram user."""
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        return None
    return await session.scalar(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == user.id)
    )


@router.callback_query(lambda callback: callback.data and callback.data.startswith("playlist:addsong:"))
async def add_song_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Start adding a song to a playlist."""
    if not callback.from_user or not callback.message or not callback.data:
        return
    playlist_id = int(callback.data.rsplit(":", maxsplit=1)[1])
    language = await get_user_language(callback.from_user.id)
    async with get_session() as session:
        playlist = await owned_playlist(session, callback.from_user.id, playlist_id)
    if playlist is None:
        await callback.answer("Playlist not found", show_alert=True)
        return
    await state.update_data(playlist_id=playlist_id)
    await state.set_state(SongAddition.waiting_for_audio)
    await callback.message.answer(MESSAGES[language]["ask_audio"])
    await callback.answer()


@router.message(SongAddition.waiting_for_audio)
async def add_song(message: Message, state: FSMContext) -> None:
    """Save an uploaded Telegram audio file to the selected playlist."""
    if not message.from_user:
        return
    language = await get_user_language(message.from_user.id)
    if message.audio is None:
        await message.answer(MESSAGES[language]["audio_only"])
        return

    state_data = await state.get_data()
    playlist_id = state_data.get("playlist_id")
    if playlist_id is None:
        await state.clear()
        return

    async with get_session() as session:
        playlist = await owned_playlist(session, message.from_user.id, playlist_id)
        if playlist is None:
            await state.clear()
            return
        session.add(
            Song(
                playlist_id=playlist_id,
                file_id=message.audio.file_id,
                title=message.audio.title,
                performer=message.audio.performer,
                duration=message.audio.duration,
            )
        )
        await session.commit()

    await state.clear()
    await message.answer(MESSAGES[language]["song_added"], reply_markup=main_menu(language))


@router.callback_query(lambda callback: callback.data and callback.data.startswith("playlist:songs:"))
async def list_songs(callback: CallbackQuery) -> None:
    """List songs belonging to a user's playlist."""
    if not callback.from_user or not callback.message or not callback.data:
        return
    playlist_id = int(callback.data.rsplit(":", maxsplit=1)[1])
    language = await get_user_language(callback.from_user.id)
    async with get_session() as session:
        playlist = await owned_playlist(session, callback.from_user.id, playlist_id)
        songs = []
        if playlist:
            result = await session.scalars(
                select(Song).where(Song.playlist_id == playlist_id).order_by(Song.id)
            )
            songs = list(result)
    if playlist is None:
        await callback.answer("Playlist not found", show_alert=True)
    elif not songs:
        await callback.message.answer(MESSAGES[language]["no_songs"])
        await callback.answer()
    else:
        await callback.message.answer(MESSAGES[language]["songs"])
        for song in songs:
            label = song.title or song.performer or "Untitled song"
            await callback.message.answer(
                f"🎵 {label}", reply_markup=song_actions(song.id, language)
            )
        await callback.answer()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("song:delete:"))
async def delete_song(callback: CallbackQuery) -> None:
    """Delete a song only if it belongs to one of the user's playlists."""
    if not callback.from_user or not callback.message or not callback.data:
        return
    song_id = int(callback.data.rsplit(":", maxsplit=1)[1])
    language = await get_user_language(callback.from_user.id)
    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        if user:
            await session.execute(
                delete(Song).where(
                    Song.id == song_id,
                    Song.playlist_id.in_(select(Playlist.id).where(Playlist.user_id == user.id)),
                )
            )
            await session.commit()
    await callback.message.edit_text(MESSAGES[language]["song_deleted"])
    await callback.answer()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("song:play:"))
async def send_song_again(callback: CallbackQuery) -> None:
    """Send the selected audio file back to its owner."""
    if not callback.from_user or not callback.message or not callback.data:
        return
    song_id = int(callback.data.rsplit(":", maxsplit=1)[1])
    async with get_session() as session:
        user = await session.scalar(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        song = None
        if user:
            song = await session.scalar(
                select(Song)
                .join(Playlist, Song.playlist_id == Playlist.id)
                .where(Song.id == song_id, Playlist.user_id == user.id)
            )
    if song is None:
        await callback.answer("Song not found", show_alert=True)
        return
    await callback.message.answer_audio(
        audio=song.file_id,
        title=song.title,
        performer=song.performer,
        duration=song.duration,
    )
    await callback.answer()


def create_dispatcher() -> Dispatcher:
    """Create and configure the update dispatcher."""
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


def create_bot() -> Bot:
    """Create a Telegram bot using the configured token."""
    return Bot(token=get_bot_token())

