import logging
logger = logging.getLogger(__name__)


def cont_message(selected_site, page_view=None):
    message = None
    help = None

    if selected_site.lower() == "libby":
        message = (
            "Libby Setup Instructions:\n\n"
            "Before continuing, please ensure:\n"
            "1. Your book is open and is the active tab in Microsoft Edge\n"
            "2. Microsoft Edge is in fullscreen mode (F11)\n"
            "3. You're on the first page of the book\n"
            "4. You know the appropriate capture area size\n"
            "5. Article button is set to 'Never'\n\n"
            "Tip: Press Esc to pause the process at any time\n"
            "Press Help for detailed configuration guidance"
        )

        help = [
            {
                "label": (
                    "1. Page View Configuration:\n"
                    "   - Use 'Arrow Up/Down' keys to toggle the menu bar\n"
                    "   - Set your page view (single or double pages) using the circled button"
                ),
                "image_path": "images/libby_page_view_button.png"
            },
            {
                "label": (
                    "2. Appearance Settings:\n"
                    "   - Click the Appearance button to adjust:\n"
                    "     • Font style and size\n"
                    "     • Color theme\n"
                    "     • Article button settings"
                ),
                "image_path": "images/libby_apperance_button.png"
            },
            {
                "label": (
                    "3. Critical Setting:\n"
                    "   - Under Appearance, ensure Article Button is set to 'Never'\n"
                    "   - Note: Font/theme changes may affect capture area size"
                ),
                "image_path": "images/libby_article_button.png"
            },
            {
                "label": (
                    "4. Final Preparation:\n"
                    "   - Close all menus before continuing\n"
                    "   - Click '^' to close Appearance menu if needed\n"
                    "   - Use Arrow keys to close the top Libby menu"
                )
            },
            {
                "label": (
                    "5. Capture Area Reminder:\n"
                    "   - Remember to account for your new settings\n"
                    "   - when determining capture area size"
                )
            }
        ]

    elif selected_site.lower() == "hoopla":
        message = (
            "Hoopla Setup Instructions:\n\n"
            "Before continuing, please ensure:\n"
            "1. Your book is open in Microsoft Edge (active tab)\n"
            "2. Edge is in fullscreen mode (F11 or Fn+F11)\n"
            "3. Verify correct page count in fullscreen mode\n"
            "4. You're on the first page\n"
            "5. 'Calculating pages' message has disappeared\n\n"
            "Note: Hoopla may temporarily unload during setup\n"
            "Tip: Press Esc to pause the process at any time\n"
            "Press Help for configuration details"
        )

        help = [
            {
                "label": (
                    "1. Access Menu:\n"
                    "   - Click the menu button to change:\n"
                    "     • Color scheme\n"
                    "     • Text size\n"
                    "     • Other reading preferences"
                ),
                "image_path": "images/hoopla_menu_button.png"
            },
            {
                "label": "2. Open Settings:\n   - Click the Settings button to continue customization",
                "image_path": "images/hoopla_settings_button.png"
            },
            {
                "label": (
                    "3. Customize Reading Experience:\n"
                    "   - Adjust:\n"
                    "     • Theme (light/dark)\n"
                    "     • Text size\n"
                    "     • Line spacing\n"
                    "     • Other preferences"
                )
            },
            {
                "label": (
                    "4. Important Final Step:\n"
                    "   - Wait for 'Calculating pages' to disappear\n"
                    "   - This appears at the bottom of the screen"
                ),
                "image_path": "images/hoopla_calculating_pages.png"
            },
            {
                "label": (
                    "5. Capture Area Note:\n"
                    "   - Remember to account for your new settings\n"
                    "   - when determining capture area size"
                )
            }
        ]

    return message, help
