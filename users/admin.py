from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # 📊 Список пользователей
    list_display = (
        'telegram_id_link', 'full_name', 'trial_status_badge', 'premium_status', 'age_display', 'last_login_display')

    list_display_links = ('telegram_id_link', 'full_name')
    list_filter = (
        'trial_status', 'is_premium', 'gender', 'is_active', 'is_staff', ('birth_date', admin.DateFieldListFilter),)

    search_fields = ('telegram_id', 'telegram_username', 'first_name', 'last_name', 'username')

    readonly_fields = ('telegram_id', 'created_at', 'last_login_display', 'trial_days_left', 'premium_days_left')

    fieldsets = (('👤 Основная информация', {
        'fields': ('telegram_id', ('first_name', 'last_name'), 'username', 'telegram_username', 'language_code'),
        'classes': ('wide', 'extrapretty')}),

                 ('📊 Профиль пользователя', {'fields': (('gender', 'birth_date'), ('height', 'weight')),
                                             'classes': ('collapse', 'wide')}),

                 ('🎯 Подписка и пробный период', {'fields': (
                     ('trial_end_date', 'trial_days_left'),
                     'is_premium', ('premium_end_date', 'premium_days_left')),
                     'classes': ('wide',)}),

                 ('🔐 Системная информация', {'fields': (
                     'is_active', 'is_staff', 'is_superuser', ('date_joined', 'last_login_display'), 'created_at'),
                     'classes': ('collapse',)}),

                 ('📝 Дополнительная информация', {'fields': ('meta',), 'classes': ('collapse',)}))

    # 📋 Дополнительные действия
    actions = ['activate_trial', 'deactivate_trial', 'grant_premium']

    # 📱 Отображение в списке
    def telegram_id_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.telegram_id)

    telegram_id_link.short_description = 'Telegram ID'
    telegram_id_link.admin_order_field = 'telegram_id'

    def full_name(self, obj):
        name_parts = []
        if obj.first_name:
            name_parts.append(obj.first_name)
        if obj.last_name:
            name_parts.append(obj.last_name)

        if name_parts:
            full_name = ' '.join(name_parts)
            if obj.telegram_username:
                return format_html('{} <br><small style="color: #666;">@{}</small>', full_name, obj.telegram_username)
            return full_name
        return obj.telegram_username or 'Без имени'

    full_name.short_description = 'Имя пользователя'

    def trial_status_badge(self, obj):
        status_colors = {'NOT_STARTED': 'gray', 'IN_PROGRESS': 'blue', 'ENDED': 'red'}
        status_texts = {'NOT_STARTED': 'Не начат', 'IN_PROGRESS': 'Активен', 'ENDED': 'Завершен'}

        color = status_colors.get(obj.trial_status, 'gray')
        text = status_texts.get(obj.trial_status, 'Неизвестно')

        return format_html('<span style="background: {}; color: white; padding: 2px 8px; '
                           'border-radius: 12px; font-size: 11px;">{}</span>', color, text)

    trial_status_badge.short_description = 'Пробный период'

    def premium_status(self, obj):
        if obj.is_premium:
            if obj.premium_end_date and obj.premium_end_date < timezone.now():
                return format_html('<span style="background: #ff4757; color: white; padding: 2px 8px; '
                                   'border-radius: 12px; font-size: 11px;">Истек</span>')
            return format_html('<span style="background: #2ed573; color: white; padding: 2px 8px; '
                               'border-radius: 12px; font-size: 11px;">Активен</span>')
        return format_html('<span style="background: #a4b0be; color: white; padding: 2px 8px; '
                           'border-radius: 12px; font-size: 11px;">Неактивен</span>')

    premium_status.short_description = 'Премиум'

    def age_display(self, obj):
        if obj.birth_date:
            today = timezone.now().date()
            age = today.year - obj.birth_date.year - (
                    (today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
            return f"{age} лет"
        return "—"

    age_display.short_description = 'Возраст'

    def last_login_display(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%d.%m.%Y %H:%M')
        return "Никогда"

    last_login_display.short_description = 'Последний вход'

    def trial_status_badge_display(self, obj):
        return self.trial_status_badge(obj)

    trial_status_badge_display.short_description = 'Статус пробного периода'

    def trial_days_left(self, obj):
        if obj.trial_end_date and obj.trial_status == 'IN_PROGRESS':
            delta = obj.trial_end_date - timezone.now()
            if delta.days > 0:
                return f"{delta.days} дней осталось"
            return "Заканчивается сегодня"
        return "—"

    trial_days_left.short_description = 'Осталось дней'

    def premium_status_display(self, obj):
        return self.premium_status(obj)

    premium_status_display.short_description = 'Статус премиума'

    def premium_days_left(self, obj):
        if obj.is_premium and obj.premium_end_date:
            delta = obj.premium_end_date - timezone.now()
            if delta.days > 0:
                return f"{delta.days} дней осталось"
            elif delta.days == 0:
                return "Заканчивается сегодня"
            return "Истек"
        return "—"

    premium_days_left.short_description = 'Осталось дней премиума'

    # ⚡ Действия
    def activate_trial(self, request, queryset):
        for user in queryset:
            if user.trial_status == 'NOT_STARTED':
                user.trial_status = 'IN_PROGRESS'
                user.trial_end_date = timezone.now() + timezone.timedelta(days=7)
                user.save()
        self.message_user(request, "Пробный период активирован для выбранных пользователей")

    activate_trial.short_description = "Активировать пробный период"

    def deactivate_trial(self, request, queryset):
        queryset.update(trial_status='ENDED')
        self.message_user(request, "Пробный период деактивирован")

    deactivate_trial.short_description = "Завершить пробный период"

    def grant_premium(self, request, queryset):
        for user in queryset:
            user.is_premium = True
            user.premium_end_date = timezone.now() + timezone.timedelta(days=30)
            user.save()
        self.message_user(request, "Премиум доступ выбранным пользователям")

    grant_premium.short_description = "Выдать премиум доступ"

    # 🎨 Стилизация
    class Media:
        css = {'all': (
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css', '/static/admin/css/custom.css',)}

    # 📈 Порядок полей
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not obj:  # При создании нового пользователя
            return (('👤 Основная информация', {'fields': ('telegram_id', 'first_name', 'last_name', 'username')}),)
        return fieldsets
