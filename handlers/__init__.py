from aiogram import Router
from .main_menu import router as main_menu_router
from .announcement.annoucement import router as annoucement_menu_router
from .developer.handlers_developer import router as developer_menu_router
from .feedback.handlers_feedback import router as feedback_menu_router
from .homework.handlers_homework import router as homework_menu_router


router = Router()
router.include_router(main_menu_router)
router.include_router(annoucement_menu_router)
router.include_router(developer_menu_router)
router.include_router(feedback_menu_router)
router.include_router(homework_menu_router)
