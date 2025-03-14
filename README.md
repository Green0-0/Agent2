### Note: Agent2 is WIP, every update will introduce breaking changes (Also only support for Python right now)

### Note2: Agent2 is for *developers*, not users. If you don't understand how an LLM works, or can't understand code to the point that an LLM has to write all of it for you, Agent2 isn't for you. This library will not babysit you.

So, what features should a good agentic library have?
1. The ability to scale: GPUs should be fully utilized, and the more compute, the better the end result.
2. Full customizability: If a model doesn't work with a given prompt, the developer should be able to tune it until it does.
3. Effective tools: The least amount of work should be required of the LLM; the most amount of work should be done by the agentic library.

Agent2 achieves this with:
1. Agent parallelization, model ensembling: Run different agents in parallel, aggregate results together. Use different models for different subtasks. Recommended: vLLM, LMDeploy, Exllama
2. Full customizability: Pick the tools you want, the prompts you want to use, and the tool formatter (codeact, json, xml, and even markdown) you would like to use. Tools have been adjusted with the goal of allowing even 7b models to become agents.
3. Tree-sitter and automatic indentation allows better lookup and more consistent code replacements, decreasing the chance of formatting issues.

Moreover:
- Agent2 only requires two seperate libraries: tree-sitter=0.21.3 and tree-sitter-languages. No langchain, no langgraph, just pure prompting. Streamlit is optional if you want the UI, sentence_transformers is optional if you want embedding models (note: currently not tested because my laptop with only 16gb of ram can't handle it)
- Agent2 comes with a UI to streamline building and running agents, however, Agent2's functionality is not strictly dependent on the UI.

Getting started:
1. Clone this repo:
``git clone https://github.com/Green0-0/Agent2``
2. Install it:
``pip install -e``
3. Do whatever you intended to do with agent2 in the first place

Using the streamlit UI:
1. Install streamlit:
``pip install streamlit``
2. Run the agent builder library:
``streamlit run agent2/ui/agent_builder.py``
3. To test an agent, use the experimental demo runner (it is not fully functional and only serves for demonstration), you will have to configure your LLM endpoint:
``streamlit run agent2/ui/experimental_demo_runner.py``

Kaggle notebook:
1. Open:
``https://www.kaggle.com/code/green000/agent2-v0-01-competition-notebook`` (Note this is v0.01, v0.02 will be released soon)
2. Run it

Python code:
[Detailed guide TBA, check the examples in the examples folder. You will need an LLM endpoint configured.]

Notes on building agents:
- It is not recommended to use more than 4 tools on an agent. This is because:
    - Tools clog up the context, small local LLMs aren't like Claude Sonnet and cannot handle this
    - LLMs suck at using the right tools at the right time; once I had a list_dir tool and Qwen-Coder would sometimes insist on repeatedly using it to find a file instead of just searching for the file
    - Recommended tools: view_element_at, search, open_element. View_element is okay, but view_element_at (inspired by openhands) works much better. Replace_element works, but open_element more consistently enables LLMs that aren't familiar with tool use to get the code edits correctly without hallucinating.
    - AVOID: replace_element_at, replace_lines, replace_block: These are terrible on models not trained on them.
- Make sure to describe the tool calling format. See the example agents for how to do so properly, but there's more ways to do so.

TODO (Urgent):
- Fix up codebase:
    - Finish documentation
    - Organize code
    - Completely redo tests (all of them are outdated and broken because of updates)
- Finish testing embeddings model
- Batch recursive ensembling (hard)
- Consider OpenAI tool calling format
- Create file, write file, open file

Experimental Ideas:
- Parse PDFs and docx to markdown 
- Markdown support (with element parsing and embeddings models, allowing agent2 to work on a data corpus like it works on a codebase); a similar thing can be done for web search, but this is far into the future
- [PUT ON HOLD BECAUSE THIS DOES NOT PLAY NICELY WITH CODEACT AGENTS] Context decay: Replace past tools with a summarized version after a set number of turns to heavily reduce context use
- Use tool binding for confirmation messages when LLMs accidentally delete elements
- An agent2 GRPO training library with Unsloth compatibility
- A set of agent2 benchmarks, inspired by aider and SWE-bench, testing things like code retrieval, refactoring, test writing; example: "Find the method my_method which computes the value of x using y by first computing z. Clean up this method by creating a helper method, my_helper, which computes z, and update my_method accordingly. The combined number of lines of the helper and method should be 5 less than it previously was."

Will be done someday:
- A better agent builder UI
- A set of agent runner UIs, each doing something different: some will use an ensemble, some will not, etc
- A set of recommended model ensembles for different tasks, and general usage guides

PRs are accepted! In particular, support for more languages is needed, currently only python works; check agent2/formatting/parsers for things that need to be done.

# Updates:
3/14/25 - v0.03 Improved viewing and editing tools, unified all searching tools
3/10/25 - v0.02 Finish tools, open_element_at, more examples, slight tool changes, depreciated codeblock cache based tools because they were garbage
3/2/25 - v0.01 Preview is ready... 

If this repo has helped you, give it a star!