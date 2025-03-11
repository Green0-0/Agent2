# Note: Agent2 is WIP, every update will introduce breaking changes!!! (Also only support for Python right now)

# Note2: Agent2 is for *developers*, not users. If you don't understand how an LLM works, or can't understand code to the point that an LLM has to write all of it for you, Agent2 isn't for you. This library will not babysit you.

So, what features should a good agentic library have?
1. The ability to scale: GPUs should be fully utilized, and the more compute, the better the end result.
2. Full customizability: If a model doesn't work with a given prompt, the developer should be able to tune it until it does.
3. Effective tools: The least amount of work should be required of the LLM; the most amount of work should be done by the agentic library.

Agent2 achieves this with:
1. Parallel model ensembles (and soon recursive model ensembles): Run different agents in parallel, aggregate results together. Use different models for different subtasks. Recommended: vLLM, LMDeploy, Exllama
2. Full customizability: Pick the tools you want, the prompts you want to use, and the tool formatter (codeact, json, xml, and even markdown) you would like to use. Tools have been finetuned with the goal of allowing even 7b models to become agents.
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
3. Run the agent runner library, you will have to configure your LLM endpoint:
``streamlit run agent2/ui/agent_runner.py``

Kaggle notebook:
1. Open:
`` https://www.kaggle.com/code/green000/agent2-v0-01-competition-notebook`` (Note this is v0.01, v0.02 will be released soon)``
2. Run it

Python code:
[Detailed guide TBA, check the examples in the examples folder. You will need an LLM endpoint configured.]

Notes on building agents:
- It is highly recommended you check all the formatting checkboxes. These prevent your agent from making serious misformatting errors.
- It is not recommended to use more than 4 tools on an agent. This is because:
    - Tools clog up the context, small local LLMs aren't like Claude Sonnet and cannot handle this
    - LLMs suck at using the right tools at the right time; once I had a list_dir tool and Qwen-Coder would sometimes insist on repeatedly using it to find a file instead of just searching for the file
    - Recommended tools: view_element_at, search_elements, open_element. View_element is okay, but view_element_at (inspired by openhands) works much better. Replace_element_at works, but open_element more consistently enables LLMs that aren't familiar with tool use to get the code edits correctly without hallucinating. There is currently some issues (not literal issues, but LLM issues) with open_element_at, use with caution.
- Make sure to describe the tool calling format. See the example agents for how to do so properly, but there's more ways to do so.

TODO (Urgent):
- Fix up codebase:
    - Add comments and documentation to everything
    - Organize code
    - Update tests (they fail because of several formatting changes introduced by v0.02)
- Finish testing embeddings model
- Add request_edit to enable easy ensembling between two agents
- Fully recursive ensembling
- Consider OpenAI tool calling format, check if its useful
- Create file, write file, open file

Experimental Ideas:
- Parse PDFs and docx to markdown 
- Markdown support (with element parsing and embeddings models, allowing agent2 to work on a data corpus like it works on a codebase); a similar thing can be done for web search, but this is far far into the future
- Automatic context manager: Replace past tools with a summarized version to heavily slash down on context use (Maybe support for different context management strategies?)
- An agent2 GRPO training library with Unsloth compatibility
- A set of agent2 benchmarks, inspired by aider and SWE-bench, testing things like code retrieval, refactoring, test writing; example: "Find the method my_method which computes the value of x using y by first computing z. Clean up this method by creating a helper method, my_helper, which computes z, and update my_method accordingly. The combined number of lines of the helper and method should be 5 less than it previously was."

Will be done someday:
- A better agent builder UI
- A set of agent runner UIs, each doing something different: some will use an ensemble, some will not, etc
- A set of recommended model ensembles for different tasks, and general usage guides
- Support for more languages: Note that originally, the library I reworked into Agent2 had half-broken (but also half-functional, depending on how you look at it) support for java, javascript, c++, typescript, and more. But as someone with no understanding of tree-sitter, all the language parsers are generated using deepseek r1, and manually hand tested.

# Updates:
3/10/25 - v0.02 Finish tools, open_element_at, more examples, slight tool changes, depreciated codeblock cache based tools because they were garbage
3/2/25 - v0.01 Preview is ready... 