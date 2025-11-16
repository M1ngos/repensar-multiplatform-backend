"""Create blog tables

Revision ID: 011
Revises: 010
Create Date: 2025-11-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    """Create blog tables for posts, categories, and tags."""

    # Create blog_categories table
    op.create_table(
        'blog_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_blog_categories_name', 'blog_categories', ['name'])
    op.create_index('ix_blog_categories_slug', 'blog_categories', ['slug'])

    # Create blog_tags table
    op.create_table(
        'blog_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_blog_tags_name', 'blog_tags', ['name'])
    op.create_index('ix_blog_tags_slug', 'blog_tags', ['slug'])

    # Create blog_posts table
    op.create_table(
        'blog_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('featured_image_url', sa.String(length=500), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id']),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_blog_posts_title', 'blog_posts', ['title'])
    op.create_index('ix_blog_posts_slug', 'blog_posts', ['slug'])
    op.create_index('ix_blog_posts_status', 'blog_posts', ['status'])
    op.create_index('ix_blog_posts_author_id', 'blog_posts', ['author_id'])
    op.create_index('ix_blog_posts_published_at', 'blog_posts', ['published_at'])

    # Create blog_post_categories junction table
    op.create_table(
        'blog_post_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('blog_post_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['blog_post_id'], ['blog_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['blog_categories.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_blog_post_categories_blog_post_id', 'blog_post_categories', ['blog_post_id'])
    op.create_index('ix_blog_post_categories_category_id', 'blog_post_categories', ['category_id'])

    # Create blog_post_tags junction table
    op.create_table(
        'blog_post_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('blog_post_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['blog_post_id'], ['blog_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['blog_tags.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_blog_post_tags_blog_post_id', 'blog_post_tags', ['blog_post_id'])
    op.create_index('ix_blog_post_tags_tag_id', 'blog_post_tags', ['tag_id'])


def downgrade():
    """Drop blog tables."""
    op.drop_index('ix_blog_post_tags_tag_id', table_name='blog_post_tags')
    op.drop_index('ix_blog_post_tags_blog_post_id', table_name='blog_post_tags')
    op.drop_table('blog_post_tags')

    op.drop_index('ix_blog_post_categories_category_id', table_name='blog_post_categories')
    op.drop_index('ix_blog_post_categories_blog_post_id', table_name='blog_post_categories')
    op.drop_table('blog_post_categories')

    op.drop_index('ix_blog_posts_published_at', table_name='blog_posts')
    op.drop_index('ix_blog_posts_author_id', table_name='blog_posts')
    op.drop_index('ix_blog_posts_status', table_name='blog_posts')
    op.drop_index('ix_blog_posts_slug', table_name='blog_posts')
    op.drop_index('ix_blog_posts_title', table_name='blog_posts')
    op.drop_table('blog_posts')

    op.drop_index('ix_blog_tags_slug', table_name='blog_tags')
    op.drop_index('ix_blog_tags_name', table_name='blog_tags')
    op.drop_table('blog_tags')

    op.drop_index('ix_blog_categories_slug', table_name='blog_categories')
    op.drop_index('ix_blog_categories_name', table_name='blog_categories')
    op.drop_table('blog_categories')
