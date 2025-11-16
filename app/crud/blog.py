# app/crud/blog.py
from sqlmodel import Session, select, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
import re

from app.models.blog import (
    BlogPost, Category, Tag, BlogPostCategory, BlogPostTag, BlogPostStatus
)
from app.models.user import User
from app.schemas.blog import (
    BlogPostCreate, BlogPostUpdate, CategoryCreate, CategoryUpdate,
    TagCreate, TagUpdate
)


def generate_slug(text: str, db: Session, model_class) -> str:
    """Generate a unique slug from text."""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special characters
    slug = re.sub(r'[-\s]+', '-', slug)  # Replace spaces/multiple hyphens with single hyphen
    slug = slug.strip('-')  # Remove leading/trailing hyphens

    # Ensure uniqueness
    original_slug = slug
    counter = 1
    while True:
        existing = db.exec(select(model_class).where(model_class.slug == slug)).first()
        if not existing:
            break
        slug = f"{original_slug}-{counter}"
        counter += 1

    return slug


class BlogCRUD:
    # ============ Blog Post Operations ============

    def create_blog_post(
        self,
        db: Session,
        post_data: BlogPostCreate,
        author_id: int
    ) -> BlogPost:
        """Create a new blog post."""
        # Generate slug from title
        slug = generate_slug(post_data.title, db, BlogPost)

        # Create the blog post
        blog_post = BlogPost(
            **post_data.model_dump(exclude={'category_ids', 'tag_ids'}),
            slug=slug,
            author_id=author_id
        )

        # Set published_at if status is published
        if blog_post.status == BlogPostStatus.published:
            blog_post.published_at = datetime.utcnow()

        db.add(blog_post)
        db.commit()
        db.refresh(blog_post)

        # Associate categories
        if post_data.category_ids:
            for category_id in post_data.category_ids:
                blog_post_category = BlogPostCategory(
                    blog_post_id=blog_post.id,
                    category_id=category_id
                )
                db.add(blog_post_category)

        # Associate tags
        if post_data.tag_ids:
            for tag_id in post_data.tag_ids:
                blog_post_tag = BlogPostTag(
                    blog_post_id=blog_post.id,
                    tag_id=tag_id
                )
                db.add(blog_post_tag)

        db.commit()
        db.refresh(blog_post)
        return blog_post

    def get_blog_post(self, db: Session, post_id: int) -> Optional[BlogPost]:
        """Get blog post by ID."""
        return db.get(BlogPost, post_id)

    def get_blog_post_by_slug(self, db: Session, slug: str) -> Optional[BlogPost]:
        """Get blog post by slug."""
        return db.exec(select(BlogPost).where(BlogPost.slug == slug)).first()

    def get_blog_posts(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 10,
        status: Optional[BlogPostStatus] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        author_id: Optional[int] = None,
        search: Optional[str] = None,
        include_drafts: bool = False
    ) -> tuple[List[BlogPost], int]:
        """Get blog posts with filtering options. Returns (posts, total_count)."""
        query = select(BlogPost)
        count_query = select(func.count(BlogPost.id))

        # Apply filters
        conditions = []

        if status:
            conditions.append(BlogPost.status == status)
        elif not include_drafts:
            conditions.append(BlogPost.status == BlogPostStatus.published)

        if author_id:
            conditions.append(BlogPost.author_id == author_id)

        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    BlogPost.title.ilike(search_pattern),
                    BlogPost.excerpt.ilike(search_pattern),
                    BlogPost.content.ilike(search_pattern)
                )
            )

        # Filter by category slug
        if category:
            cat_obj = db.exec(select(Category).where(Category.slug == category)).first()
            if cat_obj:
                post_ids_query = select(BlogPostCategory.blog_post_id).where(
                    BlogPostCategory.category_id == cat_obj.id
                )
                post_ids = [row for row in db.exec(post_ids_query).all()]
                if post_ids:
                    conditions.append(BlogPost.id.in_(post_ids))
                else:
                    # No posts in this category
                    return [], 0

        # Filter by tag slug
        if tag:
            tag_obj = db.exec(select(Tag).where(Tag.slug == tag)).first()
            if tag_obj:
                post_ids_query = select(BlogPostTag.blog_post_id).where(
                    BlogPostTag.tag_id == tag_obj.id
                )
                post_ids = [row for row in db.exec(post_ids_query).all()]
                if post_ids:
                    conditions.append(BlogPost.id.in_(post_ids))
                else:
                    # No posts with this tag
                    return [], 0

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        total = db.exec(count_query).first() or 0

        # Apply pagination and ordering
        query = query.order_by(BlogPost.published_at.desc(), BlogPost.created_at.desc())
        query = query.offset(skip).limit(limit)

        posts = db.exec(query).all()
        return posts, total

    def update_blog_post(
        self,
        db: Session,
        post_id: int,
        post_data: BlogPostUpdate
    ) -> Optional[BlogPost]:
        """Update blog post."""
        blog_post = db.get(BlogPost, post_id)
        if not blog_post:
            return None

        update_data = post_data.model_dump(exclude_unset=True, exclude={'category_ids', 'tag_ids'})

        # Update slug if title changed
        if 'title' in update_data and update_data['title'] != blog_post.title:
            update_data['slug'] = generate_slug(update_data['title'], db, BlogPost)

        # Handle status change to published
        if 'status' in update_data:
            if update_data['status'] == BlogPostStatus.published and blog_post.status != BlogPostStatus.published:
                update_data['published_at'] = datetime.utcnow()
            elif update_data['status'] == BlogPostStatus.draft:
                update_data['published_at'] = None

        # Update fields
        for field, value in update_data.items():
            setattr(blog_post, field, value)

        blog_post.updated_at = datetime.utcnow()

        # Update categories if provided
        if post_data.category_ids is not None:
            # Remove existing associations
            db.exec(
                select(BlogPostCategory).where(BlogPostCategory.blog_post_id == post_id)
            )
            for bpc in db.exec(select(BlogPostCategory).where(BlogPostCategory.blog_post_id == post_id)).all():
                db.delete(bpc)

            # Add new associations
            for category_id in post_data.category_ids:
                blog_post_category = BlogPostCategory(
                    blog_post_id=post_id,
                    category_id=category_id
                )
                db.add(blog_post_category)

        # Update tags if provided
        if post_data.tag_ids is not None:
            # Remove existing associations
            for bpt in db.exec(select(BlogPostTag).where(BlogPostTag.blog_post_id == post_id)).all():
                db.delete(bpt)

            # Add new associations
            for tag_id in post_data.tag_ids:
                blog_post_tag = BlogPostTag(
                    blog_post_id=post_id,
                    tag_id=tag_id
                )
                db.add(blog_post_tag)

        db.commit()
        db.refresh(blog_post)
        return blog_post

    def delete_blog_post(self, db: Session, post_id: int) -> bool:
        """Delete blog post."""
        blog_post = db.get(BlogPost, post_id)
        if not blog_post:
            return False

        # Delete associations first
        for bpc in db.exec(select(BlogPostCategory).where(BlogPostCategory.blog_post_id == post_id)).all():
            db.delete(bpc)
        for bpt in db.exec(select(BlogPostTag).where(BlogPostTag.blog_post_id == post_id)).all():
            db.delete(bpt)

        db.delete(blog_post)
        db.commit()
        return True

    def publish_blog_post(self, db: Session, post_id: int) -> Optional[BlogPost]:
        """Publish a blog post."""
        blog_post = db.get(BlogPost, post_id)
        if not blog_post:
            return None

        blog_post.status = BlogPostStatus.published
        blog_post.published_at = datetime.utcnow()
        blog_post.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(blog_post)
        return blog_post

    def unpublish_blog_post(self, db: Session, post_id: int) -> Optional[BlogPost]:
        """Unpublish a blog post (revert to draft)."""
        blog_post = db.get(BlogPost, post_id)
        if not blog_post:
            return None

        blog_post.status = BlogPostStatus.draft
        blog_post.published_at = None
        blog_post.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(blog_post)
        return blog_post

    def get_blog_post_with_details(self, db: Session, post_id: int) -> Optional[Dict[str, Any]]:
        """Get blog post with author, categories, and tags."""
        blog_post = db.get(BlogPost, post_id)
        if not blog_post:
            return None

        # Get author
        author = db.get(User, blog_post.author_id)

        # Get categories
        category_ids = db.exec(
            select(BlogPostCategory.category_id).where(BlogPostCategory.blog_post_id == post_id)
        ).all()
        categories = [db.get(Category, cat_id) for cat_id in category_ids]

        # Get tags
        tag_ids = db.exec(
            select(BlogPostTag.tag_id).where(BlogPostTag.blog_post_id == post_id)
        ).all()
        tags = [db.get(Tag, tag_id) for tag_id in tag_ids]

        return {
            "blog_post": blog_post,
            "author": author,
            "categories": categories,
            "tags": tags
        }

    # ============ Category Operations ============

    def create_category(self, db: Session, category_data: CategoryCreate) -> Category:
        """Create a new category."""
        slug = generate_slug(category_data.name, db, Category)

        category = Category(
            **category_data.model_dump(),
            slug=slug
        )

        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    def get_category(self, db: Session, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        return db.get(Category, category_id)

    def get_category_by_slug(self, db: Session, slug: str) -> Optional[Category]:
        """Get category by slug."""
        return db.exec(select(Category).where(Category.slug == slug)).first()

    def get_categories(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Category], int]:
        """Get all categories with post counts. Returns (categories, total_count)."""
        query = select(Category).order_by(Category.name)
        count_query = select(func.count(Category.id))

        total = db.exec(count_query).first() or 0
        categories = db.exec(query.offset(skip).limit(limit)).all()

        return categories, total

    def update_category(
        self,
        db: Session,
        category_id: int,
        category_data: CategoryUpdate
    ) -> Optional[Category]:
        """Update category."""
        category = db.get(Category, category_id)
        if not category:
            return None

        update_data = category_data.model_dump(exclude_unset=True)

        # Update slug if name changed
        if 'name' in update_data and update_data['name'] != category.name:
            update_data['slug'] = generate_slug(update_data['name'], db, Category)

        for field, value in update_data.items():
            setattr(category, field, value)

        db.commit()
        db.refresh(category)
        return category

    def delete_category(self, db: Session, category_id: int) -> bool:
        """Delete category if it has no associated posts."""
        category = db.get(Category, category_id)
        if not category:
            return False

        # Check if category has associated posts
        post_count = db.exec(
            select(func.count(BlogPostCategory.id)).where(BlogPostCategory.category_id == category_id)
        ).first()

        if post_count and post_count > 0:
            return False  # Cannot delete category with posts

        db.delete(category)
        db.commit()
        return True

    def get_category_post_count(self, db: Session, category_id: int) -> int:
        """Get the number of posts in a category."""
        return db.exec(
            select(func.count(BlogPostCategory.id)).where(BlogPostCategory.category_id == category_id)
        ).first() or 0

    # ============ Tag Operations ============

    def create_tag(self, db: Session, tag_data: TagCreate) -> Tag:
        """Create a new tag."""
        slug = generate_slug(tag_data.name, db, Tag)

        tag = Tag(
            **tag_data.model_dump(),
            slug=slug
        )

        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    def get_tag(self, db: Session, tag_id: int) -> Optional[Tag]:
        """Get tag by ID."""
        return db.get(Tag, tag_id)

    def get_tag_by_slug(self, db: Session, slug: str) -> Optional[Tag]:
        """Get tag by slug."""
        return db.exec(select(Tag).where(Tag.slug == slug)).first()

    def get_tags(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Tag], int]:
        """Get all tags with post counts. Returns (tags, total_count)."""
        query = select(Tag).order_by(Tag.name)
        count_query = select(func.count(Tag.id))

        total = db.exec(count_query).first() or 0
        tags = db.exec(query.offset(skip).limit(limit)).all()

        return tags, total

    def update_tag(
        self,
        db: Session,
        tag_id: int,
        tag_data: TagUpdate
    ) -> Optional[Tag]:
        """Update tag."""
        tag = db.get(Tag, tag_id)
        if not tag:
            return None

        update_data = tag_data.model_dump(exclude_unset=True)

        # Update slug if name changed
        if 'name' in update_data and update_data['name'] != tag.name:
            update_data['slug'] = generate_slug(update_data['name'], db, Tag)

        for field, value in update_data.items():
            setattr(tag, field, value)

        db.commit()
        db.refresh(tag)
        return tag

    def delete_tag(self, db: Session, tag_id: int) -> bool:
        """Delete tag (removes all associations with posts)."""
        tag = db.get(Tag, tag_id)
        if not tag:
            return False

        # Remove associations
        for bpt in db.exec(select(BlogPostTag).where(BlogPostTag.tag_id == tag_id)).all():
            db.delete(bpt)

        db.delete(tag)
        db.commit()
        return True

    def get_tag_post_count(self, db: Session, tag_id: int) -> int:
        """Get the number of posts with a tag."""
        return db.exec(
            select(func.count(BlogPostTag.id)).where(BlogPostTag.tag_id == tag_id)
        ).first() or 0


# Create singleton instance
blog_crud = BlogCRUD()
