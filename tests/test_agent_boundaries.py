import unittest


class AgentBoundaryTest(unittest.TestCase):
    def test_derived_agent_does_not_depend_on_workspace_io_mixins(self) -> None:
        from video_atlas.agents.derived_atlas_agent import DerivedAtlasAgent

        mro_names = {cls.__name__ for cls in DerivedAtlasAgent.__mro__}

        self.assertNotIn("WorkspaceIOMixin", mro_names)
        self.assertNotIn("WorkspacePersistenceMixin", mro_names)


if __name__ == "__main__":
    unittest.main()
