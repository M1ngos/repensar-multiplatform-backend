"""Create newsletter tables

Revision ID: 012
Revises: 011
Create Date: 2025-11-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    """Create newsletter module tables."""

    # 1. Create contact_submissions table
    op.create_table(
        'contact_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_contact_submissions_email', 'contact_submissions', ['email'])
    op.create_index('ix_contact_submissions_is_read', 'contact_submissions', ['is_read'])
    op.create_index('ix_contact_submissions_created_at', 'contact_submissions', ['created_at'])

    # 2. Create newsletter_tags table
    op.create_table(
        'newsletter_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_newsletter_tags_name', 'newsletter_tags', ['name'])
    op.create_index('ix_newsletter_tags_slug', 'newsletter_tags', ['slug'])

    # 3. Create newsletter_subscribers table
    op.create_table(
        'newsletter_subscribers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('confirmation_token', sa.String(length=255), nullable=True),
        sa.Column('confirmation_expires', sa.DateTime(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('unsubscribe_token', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('subscribed_at', sa.DateTime(), nullable=False),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('unsubscribe_token'),
    )
    op.create_index('ix_newsletter_subscribers_email', 'newsletter_subscribers', ['email'])
    op.create_index('ix_newsletter_subscribers_status', 'newsletter_subscribers', ['status'])
    op.create_index('ix_newsletter_subscribers_user_id', 'newsletter_subscribers', ['user_id'])
    op.create_index('ix_newsletter_subscribers_confirmation_token', 'newsletter_subscribers', ['confirmation_token'])
    op.create_index('ix_newsletter_subscribers_unsubscribe_token', 'newsletter_subscribers', ['unsubscribe_token'])
    op.create_index('ix_newsletter_subscribers_created_at', 'newsletter_subscribers', ['created_at'])

    # 4. Create subscriber_tags junction table
    op.create_table(
        'subscriber_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscriber_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['subscriber_id'], ['newsletter_subscribers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['newsletter_tags.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_subscriber_tags_subscriber_id', 'subscriber_tags', ['subscriber_id'])
    op.create_index('ix_subscriber_tags_tag_id', 'subscriber_tags', ['tag_id'])

    # 5. Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('variables', JSON, nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_email_templates_name', 'email_templates', ['name'])
    op.create_index('ix_email_templates_slug', 'email_templates', ['slug'])
    op.create_index('ix_email_templates_is_active', 'email_templates', ['is_active'])

    # 6. Create newsletter_campaigns table
    op.create_table(
        'newsletter_campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('preview_text', sa.String(length=255), nullable=True),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('send_to_all', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('target_tag_ids', JSON, nullable=True),
        sa.Column('total_recipients', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_delivered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_opened', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_clicked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_bounced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_unsubscribed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
    )
    op.create_index('ix_newsletter_campaigns_name', 'newsletter_campaigns', ['name'])
    op.create_index('ix_newsletter_campaigns_status', 'newsletter_campaigns', ['status'])
    op.create_index('ix_newsletter_campaigns_scheduled_at', 'newsletter_campaigns', ['scheduled_at'])
    op.create_index('ix_newsletter_campaigns_created_at', 'newsletter_campaigns', ['created_at'])

    # 7. Create campaign_recipients table
    op.create_table(
        'campaign_recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('subscriber_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('open_token', sa.String(length=255), nullable=False),
        sa.Column('click_token', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['newsletter_campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subscriber_id'], ['newsletter_subscribers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('open_token'),
        sa.UniqueConstraint('click_token'),
        sa.UniqueConstraint('campaign_id', 'subscriber_id', name='uq_campaign_subscriber'),
    )
    op.create_index('ix_campaign_recipients_campaign_id', 'campaign_recipients', ['campaign_id'])
    op.create_index('ix_campaign_recipients_subscriber_id', 'campaign_recipients', ['subscriber_id'])
    op.create_index('ix_campaign_recipients_status', 'campaign_recipients', ['status'])
    op.create_index('ix_campaign_recipients_open_token', 'campaign_recipients', ['open_token'])
    op.create_index('ix_campaign_recipients_click_token', 'campaign_recipients', ['click_token'])

    # 8. Create campaign_link_clicks table
    op.create_table(
        'campaign_link_clicks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('original_url', sa.String(length=2000), nullable=False),
        sa.Column('clicked_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['recipient_id'], ['campaign_recipients.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_campaign_link_clicks_recipient_id', 'campaign_link_clicks', ['recipient_id'])
    op.create_index('ix_campaign_link_clicks_clicked_at', 'campaign_link_clicks', ['clicked_at'])


def downgrade():
    """Drop newsletter tables."""
    # Drop in reverse order of creation
    op.drop_index('ix_campaign_link_clicks_clicked_at', table_name='campaign_link_clicks')
    op.drop_index('ix_campaign_link_clicks_recipient_id', table_name='campaign_link_clicks')
    op.drop_table('campaign_link_clicks')

    op.drop_index('ix_campaign_recipients_click_token', table_name='campaign_recipients')
    op.drop_index('ix_campaign_recipients_open_token', table_name='campaign_recipients')
    op.drop_index('ix_campaign_recipients_status', table_name='campaign_recipients')
    op.drop_index('ix_campaign_recipients_subscriber_id', table_name='campaign_recipients')
    op.drop_index('ix_campaign_recipients_campaign_id', table_name='campaign_recipients')
    op.drop_table('campaign_recipients')

    op.drop_index('ix_newsletter_campaigns_created_at', table_name='newsletter_campaigns')
    op.drop_index('ix_newsletter_campaigns_scheduled_at', table_name='newsletter_campaigns')
    op.drop_index('ix_newsletter_campaigns_status', table_name='newsletter_campaigns')
    op.drop_index('ix_newsletter_campaigns_name', table_name='newsletter_campaigns')
    op.drop_table('newsletter_campaigns')

    op.drop_index('ix_email_templates_is_active', table_name='email_templates')
    op.drop_index('ix_email_templates_slug', table_name='email_templates')
    op.drop_index('ix_email_templates_name', table_name='email_templates')
    op.drop_table('email_templates')

    op.drop_index('ix_subscriber_tags_tag_id', table_name='subscriber_tags')
    op.drop_index('ix_subscriber_tags_subscriber_id', table_name='subscriber_tags')
    op.drop_table('subscriber_tags')

    op.drop_index('ix_newsletter_subscribers_created_at', table_name='newsletter_subscribers')
    op.drop_index('ix_newsletter_subscribers_unsubscribe_token', table_name='newsletter_subscribers')
    op.drop_index('ix_newsletter_subscribers_confirmation_token', table_name='newsletter_subscribers')
    op.drop_index('ix_newsletter_subscribers_user_id', table_name='newsletter_subscribers')
    op.drop_index('ix_newsletter_subscribers_status', table_name='newsletter_subscribers')
    op.drop_index('ix_newsletter_subscribers_email', table_name='newsletter_subscribers')
    op.drop_table('newsletter_subscribers')

    op.drop_index('ix_newsletter_tags_slug', table_name='newsletter_tags')
    op.drop_index('ix_newsletter_tags_name', table_name='newsletter_tags')
    op.drop_table('newsletter_tags')

    op.drop_index('ix_contact_submissions_created_at', table_name='contact_submissions')
    op.drop_index('ix_contact_submissions_is_read', table_name='contact_submissions')
    op.drop_index('ix_contact_submissions_email', table_name='contact_submissions')
    op.drop_table('contact_submissions')
