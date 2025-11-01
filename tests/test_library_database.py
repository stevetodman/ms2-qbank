"""Tests for database-backed library store."""

import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield f"sqlite:///{db_path}"
    db_path.unlink(missing_ok=True)


@pytest.fixture
def store(temp_db):
    """Create a LibraryDatabaseStore with a temporary database."""
    from src.library.db_store import LibraryDatabaseStore

    return LibraryDatabaseStore(db_path=temp_db)


class TestArticleOperations:
    """Tests for article operations."""

    def test_create_article(self, store):
        """Test creating an article."""
        article = store.create_article(
            article_id="article1",
            title="Myocardial Infarction",
            summary="Overview of MI diagnosis and management",
            body="Detailed content about MI...",
            tags=["cardiology", "emergency"],
            author="Dr. Smith",
        )

        assert article.id is not None
        assert article.article_id == "article1"
        assert article.title == "Myocardial Infarction"
        assert article.author == "Dr. Smith"
        assert article.bookmarked is False

    def test_get_article(self, store):
        """Test retrieving an article."""
        created = store.create_article(
            article_id="article1",
            title="Test Article",
            summary="Summary",
            body="Body",
        )

        retrieved = store.get_article("article1")

        assert retrieved is not None
        assert retrieved.article_id == "article1"
        assert retrieved.title == "Test Article"

    def test_get_nonexistent_article(self, store):
        """Test retrieving a non-existent article."""
        result = store.get_article("nonexistent")
        assert result is None

    def test_list_articles(self, store):
        """Test listing all articles."""
        store.create_article(
            article_id="art1", title="Article A", summary="Summary A", body="Body A"
        )
        store.create_article(
            article_id="art2", title="Article B", summary="Summary B", body="Body B"
        )

        articles = store.list_articles()

        assert len(articles) == 2
        # Should be sorted by title
        assert articles[0].title == "Article A"
        assert articles[1].title == "Article B"

    def test_list_articles_with_query(self, store):
        """Test listing articles with text search."""
        store.create_article(
            article_id="art1",
            title="Myocardial Infarction",
            summary="Heart attack overview",
            body="Content",
        )
        store.create_article(
            article_id="art2", title="Stroke", summary="Brain attack", body="Content"
        )

        # Search by title
        results = store.list_articles(query="myocardial")
        assert len(results) == 1
        assert results[0].article_id == "art1"

        # Search by summary
        results = store.list_articles(query="brain")
        assert len(results) == 1
        assert results[0].article_id == "art2"

    def test_list_articles_with_tag_filter(self, store):
        """Test listing articles filtered by tag."""
        store.create_article(
            article_id="art1",
            title="Article 1",
            summary="Summary",
            body="Body",
            tags=["cardiology", "emergency"],
        )
        store.create_article(
            article_id="art2",
            title="Article 2",
            summary="Summary",
            body="Body",
            tags=["neurology"],
        )

        results = store.list_articles(tag="cardiology")

        assert len(results) == 1
        assert results[0].article_id == "art1"

    def test_list_articles_bookmarked_only(self, store):
        """Test listing only bookmarked articles."""
        store.create_article(
            article_id="art1", title="Article 1", summary="Summary", body="Body"
        )
        art2 = store.create_article(
            article_id="art2", title="Article 2", summary="Summary", body="Body"
        )

        # Bookmark one article
        store.set_article_bookmark("art2", True)

        results = store.list_articles(bookmarked_only=True)

        assert len(results) == 1
        assert results[0].article_id == "art2"

    def test_update_article(self, store):
        """Test updating an article."""
        store.create_article(
            article_id="art1",
            title="Original Title",
            summary="Original Summary",
            body="Original Body",
            tags=["tag1"],
        )

        updated = store.update_article(
            article_id="art1",
            title="Updated Title",
            summary="Updated Summary",
            tags=["tag1", "tag2"],
        )

        assert updated.title == "Updated Title"
        assert updated.summary == "Updated Summary"
        import json
        assert json.loads(updated.tags) == ["tag1", "tag2"]

    def test_update_nonexistent_article(self, store):
        """Test updating a non-existent article raises error."""
        with pytest.raises(KeyError, match="not found"):
            store.update_article("nonexistent", title="New Title")

    def test_set_article_bookmark(self, store):
        """Test bookmarking an article."""
        store.create_article(
            article_id="art1", title="Article", summary="Summary", body="Body"
        )

        # Bookmark
        updated = store.set_article_bookmark("art1", True)
        assert updated.bookmarked is True

        # Unbookmark
        updated = store.set_article_bookmark("art1", False)
        assert updated.bookmarked is False

    def test_delete_article(self, store):
        """Test deleting an article."""
        store.create_article(
            article_id="art1", title="Article", summary="Summary", body="Body"
        )

        deleted = store.delete_article("art1")
        assert deleted is True

        # Verify it's gone
        retrieved = store.get_article("art1")
        assert retrieved is None

    def test_delete_nonexistent_article(self, store):
        """Test deleting a non-existent article."""
        deleted = store.delete_article("nonexistent")
        assert deleted is False

    def test_all_article_tags(self, store):
        """Test getting all unique article tags."""
        store.create_article(
            article_id="art1",
            title="Article 1",
            summary="Summary",
            body="Body",
            tags=["cardiology", "emergency"],
        )
        store.create_article(
            article_id="art2",
            title="Article 2",
            summary="Summary",
            body="Body",
            tags=["neurology", "cardiology"],
        )

        tags = store.all_article_tags()

        assert set(tags) == {"cardiology", "emergency", "neurology"}
        assert tags == sorted(tags)  # Should be sorted


class TestNotebookOperations:
    """Tests for notebook entry operations."""

    def test_create_note(self, store):
        """Test creating a notebook entry."""
        note = store.create_note(
            title="My Study Note",
            body="Important points about cardiology",
            tags=["study", "cardiology"],
            article_ids=["art1", "art2"],
            question_ids=["q1"],
            user_id=1,
        )

        assert note.id is not None
        assert note.note_id is not None
        assert note.title == "My Study Note"
        assert note.user_id == 1
        assert note.bookmarked is False

    def test_get_note(self, store):
        """Test retrieving a note."""
        created = store.create_note(
            title="Test Note",
            body="Test Body",
        )

        retrieved = store.get_note(created.note_id)

        assert retrieved is not None
        assert retrieved.note_id == created.note_id
        assert retrieved.title == "Test Note"

    def test_get_nonexistent_note(self, store):
        """Test retrieving a non-existent note."""
        result = store.get_note("nonexistent")
        assert result is None

    def test_list_notes(self, store):
        """Test listing all notes."""
        store.create_note(title="Note A", body="Body A")
        store.create_note(title="Note B", body="Body B")

        notes = store.list_notes()

        assert len(notes) == 2

    def test_list_notes_with_query(self, store):
        """Test listing notes with text search."""
        store.create_note(title="Cardiology Notes", body="Heart topics")
        store.create_note(title="Neurology Notes", body="Brain topics")

        # Search by title
        results = store.list_notes(query="cardiology")
        assert len(results) == 1
        assert "Cardiology" in results[0].title

        # Search by body
        results = store.list_notes(query="brain")
        assert len(results) == 1
        assert "Neurology" in results[0].title

    def test_list_notes_with_tag_filter(self, store):
        """Test listing notes filtered by tag."""
        store.create_note(title="Note 1", body="Body", tags=["cardiology", "review"])
        store.create_note(title="Note 2", body="Body", tags=["neurology"])

        results = store.list_notes(tag="cardiology")

        assert len(results) == 1
        assert results[0].title == "Note 1"

    def test_list_notes_with_article_filter(self, store):
        """Test listing notes filtered by article ID."""
        store.create_note(title="Note 1", body="Body", article_ids=["art1", "art2"])
        store.create_note(title="Note 2", body="Body", article_ids=["art3"])

        results = store.list_notes(article_id="art1")

        assert len(results) == 1
        assert results[0].title == "Note 1"

    def test_list_notes_with_question_filter(self, store):
        """Test listing notes filtered by question ID."""
        store.create_note(title="Note 1", body="Body", question_ids=["q1", "q2"])
        store.create_note(title="Note 2", body="Body", question_ids=["q3"])

        results = store.list_notes(question_id="q1")

        assert len(results) == 1
        assert results[0].title == "Note 1"

    def test_list_notes_by_user(self, store):
        """Test listing notes for a specific user."""
        store.create_note(title="User 1 Note", body="Body", user_id=1)
        store.create_note(title="User 2 Note", body="Body", user_id=2)

        results = store.list_notes(user_id=1)

        assert len(results) == 1
        assert results[0].title == "User 1 Note"

    def test_list_notes_bookmarked_only(self, store):
        """Test listing only bookmarked notes."""
        note1 = store.create_note(title="Note 1", body="Body")
        note2 = store.create_note(title="Note 2", body="Body")

        # Bookmark one note
        store.set_note_bookmark(note2.note_id, True)

        results = store.list_notes(bookmarked_only=True)

        assert len(results) == 1
        assert results[0].note_id == note2.note_id

    def test_update_note(self, store):
        """Test updating a note."""
        note = store.create_note(
            title="Original Title",
            body="Original Body",
            tags=["tag1"],
        )

        updated = store.update_note(
            note_id=note.note_id,
            title="Updated Title",
            tags=["tag1", "tag2"],
            article_ids=["art1"],
        )

        assert updated.title == "Updated Title"
        import json
        assert json.loads(updated.tags) == ["tag1", "tag2"]
        assert json.loads(updated.article_ids) == ["art1"]

    def test_update_nonexistent_note(self, store):
        """Test updating a non-existent note raises error."""
        with pytest.raises(KeyError, match="not found"):
            store.update_note("nonexistent", title="New Title")

    def test_set_note_bookmark(self, store):
        """Test bookmarking a note."""
        note = store.create_note(title="Note", body="Body")

        # Bookmark
        updated = store.set_note_bookmark(note.note_id, True)
        assert updated.bookmarked is True

        # Unbookmark
        updated = store.set_note_bookmark(note.note_id, False)
        assert updated.bookmarked is False

    def test_delete_note(self, store):
        """Test deleting a note."""
        note = store.create_note(title="Note", body="Body")

        deleted = store.delete_note(note.note_id)
        assert deleted is True

        # Verify it's gone
        retrieved = store.get_note(note.note_id)
        assert retrieved is None

    def test_delete_nonexistent_note(self, store):
        """Test deleting a non-existent note."""
        deleted = store.delete_note("nonexistent")
        assert deleted is False

    def test_all_note_tags(self, store):
        """Test getting all unique note tags."""
        store.create_note(title="Note 1", body="Body", tags=["cardiology", "review"])
        store.create_note(title="Note 2", body="Body", tags=["neurology", "cardiology"])

        tags = store.all_note_tags()

        assert set(tags) == {"cardiology", "neurology", "review"}
        assert tags == sorted(tags)  # Should be sorted
