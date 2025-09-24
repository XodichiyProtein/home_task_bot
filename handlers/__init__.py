# handlers/__init__.py
from aiogram import Router
from .main_menu import router as main_menu_router
from .dev_menu import router as dev_menu_router

router = Router()
router.include_router(main_menu_router)
router.include_router(dev_menu_router)
